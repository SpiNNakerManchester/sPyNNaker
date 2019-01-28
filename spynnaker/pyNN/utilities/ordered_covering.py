"""
Ordered Covering
================

An novel algorithm for the minimisation of SpiNNaker's multicast routing tables
devised by Andrew Mundy.

Background
----------

SpiNNaker routing tables consist of entries made up of a 32-bit key, a 32-bit
mask and a 24-bit route value. The key and mask of every entry act as a sieve
for the keys found on incoming multicast packets. Each bit of the key-mask pair
can be considered as matching 0, 1 or 2 values in the same bit of a multicast
packet key:

 =====   =====   ==================   =======
 Key     Mask    Matches Key Values   Written
 =====   =====   ==================   =======
 ``0``   ``0``   ``0`` or ``1``       ``X``
 ``0``   ``1``   ``0``                ``0``
 ``1``   ``1``   ``1``                ``1``
 ``1``   ``0``   Nothing              ``!``
 =====   =====   ==================   =======

If a packet matches the key-mask of an entry then the packet is transmitted to
the cores and links indicated by the route field.

For example, if the table were:

 ========  ========  =================
 Key       Mask      Route
 ========  ========  =================
 ``0000``  ``1111``  North, North East
 ``0111``  ``0111``  South
 ========  ========  =================

Which, from now on, will be written as::

    0000 -> N NE
    X111 -> S

Then any packets with the key ``0000`` would be sent out of the north and
north-east links. Any packets with the keys ``0111`` or ``1111`` would be sent
out of the south link only.

Entries in table are ordered, with entries at the top of the table having
higher priority than those lower down the table. Only the highest priority
entry which matches a packet is used. If, for example, the table were::

    0000 -> N NE
    1111 -> 1 2
    X111 -> S

Then packets with the keys ``0000`` and ``0111`` would be treated as before.
However, packets with the key ``1111`` would be sent to cores 1 and 2 as only
the higher priority entry has effect.

Merging routing table entries
-----------------------------

Routing tables can be minimised by merging together entries with equivalent
routes. This is done by creating a new key-mask pair with an ``X`` wherever the
key-mask pairs of any of the original entries differed.

For example, merging of the entries::

    0000 -> N
    0001 -> N

Would lead to the new entry:

    000X -> N

Which would match any of the keys matched by the original entries but no more.
In contrast the merge of ``0001`` and ``0010`` would generate the new entry
``00XX`` which would match keys matched by either of the original entries but
also ``0000`` and ``0011``.

Clearly, if we are to attempt to minimise tables such as::

    0001 -> N
    0010 -> N
    0000 -> S, SE
    0011 -> SE

We need a set of rules for:

 1. Where merged entries are to be inserted into the table
 2. Which merges are allowed

"Ordered Covering"
------------------

The algorithm implemented here, "Ordered Covering", provides the following
rule:

 * The only merges allowed are those which:

   a) would not cause one of the entries in the merge to be "hidden" below
      an entry of lesser generality than the merged entry but which matched
      any of the same keys. For example, merging ``0010`` and ``0001`` would
      not be allowed if the new entry would be placed below the existing
      entry ``000X`` as this would "hide" ``0001``.
   b) would not cause an entry "contained" within an entry of higher
      generality to be hidden by the insertion of a new entry. For example, if
      the entry ``XXXX`` had been formed by merging the entries ``0011`` and
      ``1100`` then merging of the entries ``1101`` and ``1110`` would not be
      allowed as it would cause the entry ``11XX`` to be inserted above
      ``XXXX`` in the table and would hide ``1100``.

Following these rules ensures that the minimised table will be functionally
equivalent to the original table provided that the original table was invariant
under reordering OR was provided in increasing order of generality.

As a heuristic:

 * Routing tables are to be kept sorted in increasing order of "generality",
   that is the number of ``X``s in the entry. An entry with the key-mask pair
   ``00XX`` must be placed below any entries with fewer ``X``s in their
   key-mask pairs (e.g., below ``0000`` and ``000X``).

   a) New entries must also be inserted below any entries of the same
      generality. If ``XX00`` were already present in the table the new entry
      ``0XX0`` must be inserted below it.
"""
from collections import namedtuple
from rig.routing_table import MinimisationFailedError, RoutingTableEntry
from rig.routing_table import remove_default_routes
from rig.routing_table.utils import intersect

from spinn_utilities.timer import Timer


def minimise(routing_table, target_length,
             time_to_run_for_before_raising_exception, use_timer_cut_off):
    """Reduce the size of a routing table by merging together entries where
    possible and by removing any remaining default routes.

    .. warning::

        The input routing table *must* also include entries which could be
        removed and replaced by default routing.

    .. warning::

        It is assumed that the input routing table is not in any particular
        order and may be reordered into ascending order of generality (number
        of don't cares/Xs in the key-mask) without affecting routing
        correctness.  It is also assumed that if this table is unordered it is
        at least orthogonal (i.e., there are no two entries which would match
        the same key) and reorderable.

        .. note::

            If *all* the keys in the table are derived from a single instance
            of :py:class:`~rig.bitfield.BitField` then the table is guaranteed
            to be orthogonal and reorderable.

        .. note::

            Use :py:meth:`~rig.routing_table.expand_entries` to generate an
            orthogonal table and receive warnings if the input table is not
            orthogonal.

    :type routing_table: \
        [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
    :param routing_table : Routing entries to be merged.
    :type target_length : int or None
    :param target_length: Target length of the routing table; the minimisation\
        procedure will halt once either this target is reached or no further \
        minimisation is possible. If None then the table will be made as \
        small as possible.
    :type time_to_run_for_before_raising_exception: int
    :param time_to_run_for_before_raising_exception: the time to run for \
        in seconds before raising an exception
    :param use_timer_cut_off: bool flag for is timing cutoff is to be used.
    :type use_timer_cut_off: bool
    :raises MinimisationFailedError: If the smallest table that can be \
        produced is larger than `target_length`.
    :return: the compressed routing entries
    :rtype: [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
    """
    table, _ = ordered_covering(
        routing_table=routing_table, target_length=target_length,
        no_raise=True,  use_timer_cut_off=use_timer_cut_off,
        time_to_run_for=time_to_run_for_before_raising_exception)
    return remove_default_routes.minimise(table, target_length)


def ordered_covering(
        routing_table, target_length, time_to_run_for, aliases=None,
        no_raise=False, use_timer_cut_off=False):
    """Reduce the size of a routing table by merging together entries where
    possible.

    .. warning::

        The input routing table *must* also include entries which could be
        removed and replaced by default routing.

    .. warning::

        It is assumed that the input routing table is not in any particular
        order and may be reordered into ascending order of generality (number
        of don't cares/Xs in the key-mask) without affecting routing
        correctness.  It is also assumed that if this table is unordered it is
        at least orthogonal (i.e., there are no two entries which would match
        the same key) and reorderable.

        .. note::

            If *all* the keys in the table are derived from a single instance
            of :py:class:`~rig.bitfield.BitField` then the table is guaranteed
            to be orthogonal and reorderable.

        .. note::

            Use :py:meth:`~rig.routing_table.expand_entries` to generate an
            orthogonal table and receive warnings if the input table is not
            orthogonal.

    :param routing_table: Routing entries to be merged.
    :type routing_table: \
        [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
    :type target_length : int or None
    :param target_length: Target length of the routing table; the \
        minimisation procedure will halt once either this target is reached \
        or no further minimisation is possible. If None then the table will \
        be made as small as possible.
    :type aliases : {(key, mask): {(key, mask), ...}, ...}
    :param aliases: Dictionary of which keys and masks in the routing table \
        are combinations of other (now removed) keys and masks; this allows us\
        to consider only the keys and masks the user actually cares about when\
        determining if inserting a new entry will break the correctness of the\
        table. This should be supplied when using this method to update an\
        already minimised table.
    :type no_raise : bool
    :param no_raise: If False (the default) then an error will be raised if \
        the table cannot be minimised to be smaller than `target_length` and \
        `target_length` is not None. If True then a table will be returned \
        regardless of the size of the final table.
    :param time_to_run_for: how long to run for in seconds before raises \
        exception
    :type time_to_run_for: int
    :param use_timer_cut_off: bool flag for using time cutoff
    :type use_timer_cut_off: bool
    :raises MinimisationFailedError: If the smallest table that can be \
        produced is larger than target_length` and `no_raise` is False.
    :return: Reduced routing table entries.
    :rtype: [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
    """

    timer = Timer()
    timer.start_timing()

    if aliases is None:
        aliases = dict()

    # Copy the aliases dictionary
    aliases = dict(aliases)

    # Perform an initial sort of the routing table in order of increasing
    # generality.
    routing_table = sorted(
        routing_table,
        key=lambda entry: _get_generality(entry.key, entry.mask)
    )

    while target_length is None or len(routing_table) > target_length:
        # Get the best merge
        merge = _get_best_merge(routing_table, aliases)

        # If there is no merge then stop
        if merge.goodness <= 0:
            break

        # Otherwise apply the merge, this returns a new routing table and a new
        # aliases dictionary.
        routing_table, aliases = merge.apply(aliases)

        if use_timer_cut_off:
            diff = timer.take_sample()
            if diff.total_seconds() >= time_to_run_for:
                raise MinimisationFailedError(
                    target_length, len(routing_table))

    # If the table is still too big then raise an error
    if (not no_raise and target_length is not None and
            len(routing_table) > target_length):
        raise MinimisationFailedError(target_length, len(routing_table))

    # Return the finished routing table and aliases table
    return routing_table, aliases


def _get_generality(key, mask):
    """Count the number of Xs in the key-mask pair.

    For example, there are 32 Xs in ``0x00000000/0x00000000``::

        >>> _get_generality(0x0, 0x0)
        32

    And no Xs in ``0xffffffff/0xffffffff``::

        >>> _get_generality(0xffffffff, 0xffffffff)
        0
    """
    xs = (~key) & (~mask)
    return sum(1 for i in range(32) if xs & (1 << i))


def _get_best_merge(routing_table, aliases):
    """Inspect all possible merges for the routing table and return the merge
    which would combine the greatest number of entries.

    :rtype :py:class:`~.Merge`
    """
    # Create an empty merge to start with
    best_merge = _Merge(routing_table)
    best_goodness = 0

    # Look through every merge, discarding those that are no better than the
    # best we currently know about.
    for merge in _get_all_merges(routing_table):
        # If the merge isn't sufficiently good ignore it and move on
        if merge.goodness <= best_goodness:
            continue

        # After the merge refines itself to remove entries which would either
        # be aliased under other entries or entries which would cause the
        # aliasing of other entries we check if it is better than the current
        # best merge and reject it if it isn't.
        merge = _refine_merge(merge, aliases, min_goodness=best_goodness)
        if merge.goodness > best_goodness:
            # The merge we now have a reference to is better than the best
            # merge that we've previously encountered.
            best_merge = merge
            best_goodness = merge.goodness

    # Return the best merge and the best goodness for the calling method
    return best_merge


def _get_all_merges(routing_table):
    """Get possible sets of entries to merge.

    :rtype :py:class:`~.Merge`
    """
    # Memorise entries that have been considered as part of a merge
    considered_entries = set()

    for i, entry in enumerate(routing_table):
        # If we've already considered this entry then skip
        if i in considered_entries:
            continue

        # Construct a merge by including other routing table entries below this
        # one which have equivalent routes.
        merge = {i}
        merge.update(
            j for j, other_entry in enumerate(routing_table[i+1:], start=i+1)
            if entry.route == other_entry.route
        )

        # Mark all these entries as considered
        considered_entries.update(merge)

        # If the merge contains multiple entries then yield it
        if len(merge) > 1:
            yield _Merge(routing_table, merge)


def _get_insertion_index(routing_table, generality):
    """Determine the index in the routing table where a new entry should be
    inserted.
    """
    # We insert before blocks of equivalent generality, so decrement the given
    # generality.
    generality -= 1

    # Wrapper for _get_generality which accepts a routing entry
    def gg(entry):
        return _get_generality(entry.key, entry.mask)

    # Perform a binary search through the routing table
    bottom = 0
    top = len(routing_table)
    pos = (top - bottom) // 2

    pg = gg(routing_table[pos])
    while pg != generality and bottom < pos < top:
        if pg < generality:
            bottom = pos  # Move up
        else:  # pg > generality
            top = pos  # Move down

        # Compute a new position
        pos = bottom + (top - bottom) // 2
        pg = gg(routing_table[pos])

    while (pos < len(routing_table) and
           gg(routing_table[pos]) <= generality):
        pos += 1

    return pos


class _Merge(namedtuple("_Merge", ["routing_table", "entries", "key", "mask",
                                   "generality", "goodness",
                                   "insertion_index", "sources"])):
    """Represents a potential merge of routing table entries.

    Parameters
    ----------
    routing_table : [:py:class:`~.RoutingTableEntry`, ...]
        Reference to the routing table against which the merge is defined.
    entries : {int, ...}
        Indices of entries in the routing table which are included in this
        merge.
    key : int
    mask : int
        Key and mask pair generated by this merge.
    generality : int
        Number of ``X`` s in the key-mask pair generated by this merge.
    goodness : int
        Measure of how "good" this merge is
    insertion_index : int
        Where in the routing table the entry generated would need to be
        inserted.
    sources : {Routes, ...}
        Set of Routes that packets reaching the merge may arrive from.
    """
    def __new__(cls, routing_table, entries=set()):
        # Generate the new key, mask and sources
        sources = set()
        any_ones = 0x00000000  # Wherever there is a 1 in *any* of the keys
        all_ones = 0xffffffff  # ... 1 in *all* of the keys
        all_selected = 0xffffffff  # ... 1 in *all* of the masks

        for i in entries:
            # Get the entry
            entry = routing_table[i]

            # Update the values
            any_ones |= entry.key
            all_ones &= entry.key
            all_selected &= entry.mask
            sources.update(entry.sources)

        # Compute the new mask, key and generality
        any_zeros = ~all_ones
        new_xs = any_ones ^ any_zeros
        mask = all_selected & new_xs  # Combine existing and new Xs
        key = all_ones & mask

        generality = _get_generality(key, mask)
        insertion_index = _get_insertion_index(routing_table, generality)

        # Compute the goodness of the merge
        goodness = len(entries) - 1

        return super(_Merge, cls).__new__(
            cls, routing_table, frozenset(entries), key, mask,
            generality, goodness, insertion_index, sources
        )

    def apply(self, aliases):
        """Apply the merge to the routing table it is defined against and get a
        new routing table and alias dictionary.

        Returns
        -------
        [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
            A new routing table which may be minimised further.
        {(key, mask): {(key, mask), ...}}
            A new aliases dictionary.
        """
        # Create a new routing table of the correct size
        new_size = len(self.routing_table) - len(self.entries) + 1
        new_table = [None for _ in range(new_size)]

        # Create a copy of the aliases dictionary
        aliases = dict(aliases)

        # Get the new entry
        new_entry = RoutingTableEntry(
            route=self.routing_table[next(iter(self.entries))].route,
            key=self.key, mask=self.mask, sources=self.sources
        )
        aliases[(self.key, self.mask)] = our_aliases = set([])

        # Iterate through the old table copying entries acrosss
        insert = 0
        for i, entry in enumerate(self.routing_table):
            # If this is the insertion point then insert
            if i == self.insertion_index:
                new_table[insert] = new_entry
                insert += 1

            if i not in self.entries:
                # If this entry isn't to be removed then copy it across to the
                # new table.
                new_table[insert] = entry
                insert += 1
            else:
                # If this entry is to be removed then add it to the aliases
                # dictionary.
                km = (entry.key, entry.mask)
                our_aliases.update(aliases.pop(km, {km}))

        # If inserting beyond the end of the old table then insert at the end
        # of the new table.
        if self.insertion_index == len(self.routing_table):
            new_table[insert] = new_entry

        return new_table, aliases


def _refine_merge(merge, aliases, min_goodness):
    """Remove entries from a merge to generate a valid merge which may be
    applied to the routing table.

    Parameters
    ----------
    merge : :py:class:`~.Merge`
        Initial merge to refine.
    aliases : {(key, mask): {(key, mask), ...}, ...}
        Map of key-mask pairs to the sets of key-mask pairs that they actually
        represent.
    min_goodness : int
        Reject merges which are worse than the minimum goodness.

    Returns
    -------
    :py:class:`~.Merge`
        Valid merge which may be applied to the routing table.
    """
    # Perform the down-check
    merge = _refine_downcheck(merge, aliases, min_goodness)

    # If the merge is still sufficiently good then continue to refine it.
    if merge.goodness > min_goodness:
        # Perform the up-check
        merge, changed = _refine_upcheck(merge, min_goodness)

        if changed and merge.goodness > min_goodness:
            # If the up-check removed any entries we need to re-perform the
            # down-check; but we do not need to re-perform the up-check as the
            # down check can only move the resultant merge nearer the top of
            # the routing table.
            merge = _refine_downcheck(merge, aliases, min_goodness)

    return merge


def _refine_upcheck(merge, min_goodness):
    """Remove from the merge any entries which would be covered by entries
    between their current position and the merge insertion position.

    For example, the third entry of::

        0011 -> N
        0100 -> N
        1000 -> N
        X000 -> NE

    Cannot be merged with the first two entries because that would generate the
    new entry ``XXXX`` which would move ``1000`` below the entry with the
    key-mask pair of ``X000``, which would cover it.

    Returns
    -------
    :py:class:`~.Merge`
        New merge with entries possibly removed. If the goodness of the merge
        ever drops below `min_goodness` then an empty merge will be returned.
    bool
        If the merge has been changed at all.
    """
    # Remove any entries which would be covered by entries above the merge
    # position.
    changed = False
    for i in sorted(merge.entries, reverse=True):
        # Get all the entries that are between the entry we're looking at the
        # insertion index of the proposed merged index. If this entry would be
        # covered up by any of them then we remove it from the merge.
        entry = merge.routing_table[i]
        key, mask = entry.key, entry.mask
        if any(intersect(key, mask, other.key, other.mask) for other in
               merge.routing_table[i+1:merge.insertion_index]):
            # The entry would be partially or wholly covered by another entry,
            # remove it from the merge and return a new merge.
            merge = _Merge(merge.routing_table, merge.entries - {i})
            changed = True

            # Check if the merge is sufficiently good
            if merge.goodness <= min_goodness:
                merge = _Merge(merge.routing_table)  # Replace with empty merge
                break

    # Return the final merge
    return merge, changed


def _refine_downcheck(merge, aliases, min_goodness):
    """Prune the merge to avoid it covering up any entries which are below the
    merge insertion position.

    For example, in the (non-orthogonal) table::

        00001 -> N S
        00011 -> N S
        00100 -> N S
        00X00 -> N S
        XX1XX -> 3 5

    Merging the first four entries would generate the new key-mask ``00XXX``
    which would be inserted above the entry with the key-mask ``XX1XX``.
    However ``00XXX`` would stop the key ``00110`` from reaching its correct
    route, that is ``00110`` would be covered by ``00XXX``. To avoid this one
    could just abandon the merge entirely, but a better solution is to attempt
    to reduce the merge such that it no longer covers any entries below it.

    To do this we first identify the bits that ARE ``X`` s in the merged
    key-mask but which are NOT ``X`` s in the entry that we're covering. For
    this example this is the 3rd bit. We then look to remove from the merge any
    entries which are either ``X`` s in this position OR have the same value as
    in this bit as the aliased entry. As the 4th entry in the table has an
    ``X`` in this position we remove it, and as the 3rd entry has a ``1`` we
    also remove it.  For this example we would then consider merging only the
    first two entries, leading to a new key-mask pair of ``000X1`` which can be
    safely inserted between ``00X00`` and ``XX1XX``::

        00100 -> N S
        00X00 -> N S
        000X1 -> N S
        XX1XX -> 3 5

    Returns
    -------
    :py:class:`~.Merge`
        New merge with entries possibly removed. If the goodness of the merge
        ever drops below `min_goodness` then an empty merge will be returned.
    """
    # Operation
    # ---------
    # While the merge is still better than `min_goodness` we determine which
    # entries below it in the table it covers. For each of these covered
    # entries we find which bits are Xs in the merged entry and are NOT Xs in
    # the covered entry.
    #
    # For example:
    #
    #     Merged entry:      ...0XXX1...
    #     Covered entry:     ...010XX...
    #     Bits of interest:      ^^
    #     Label used below:      mn
    #
    # NOTE:
    #   The covered entry may be of lower generality than the prospective
    #   merged entry if it is contained within the aliases dictionary (e.g.,
    #   ...010XX... may be part of
    #   ``aliases = {...XXXXX...: {..., ...010XX..., ...}, ...})``
    #
    # In this case there are 2 bits of interest highlighted. These are bits in
    # the merge entry whose value can be set (by removing entries from the
    # merge) to avoid covering the covered entry. Whenever we have multiple
    # covered entries we care only about the entries with the fewest number of
    # ``settable`` bits because these most constrain which entries we may
    # remove from the merge to avoid covering up the lower entry.
    #
    # NOTE:
    #   * If there is only 1 ``settable`` bit then we are very constrained in
    #     terms of which entries must be removed from the merge to avoid
    #     covering a lower entry.
    #   * If there are no ``settable`` bits then we cannot possibly avoid
    #     covering the lower entry - the only correct action is to return an
    #     empty merge.
    #
    # Assuming that there were no covered entries without any ``settable`` bits
    # (that is ``stringency > 0``) then ``bits_and_vals`` contains pairs of
    # bits and boolean values which indicate which values need to be removed
    # from which bit positions to avoid covering up lower entries. If the
    # example above were the only covered entry then ``bits_and_vals`` would
    # contain ``(m, True)`` to indicate that all entries containing Xs or 1s in
    # the left-most bit of interest could be removed to avoid the covered entry
    # and ``(n, False)`` to indicate that all entries containing Xs or 0s in
    # the right-most bit of interest could be removed to avoid covering the
    # entry.
    #
    # NOTE:
    #   ``bits_and_vals`` consists of a set of options (e.g., we *could* remove
    #   all entries with Xs or 1s in bit ``m`` *or* we could remove all entries
    #   with Xs or 0s in bit ``n``, either would resolve the above covering).
    #
    # To determine which course of action to take we build a dictionary mapping
    # each of the pairs in ``bits_and_vals`` to the entries that would need to
    # be removed to "set" that bit in the merged entry. For example, we might
    # end up with:
    #
    #     options = {(m, True): {1, 4, 5},
    #                (n, False): {3, 7}}
    #
    # Indicating that we'd need to remove entries 1, 4 and 5 from the merge to
    # "set" the mth bit of the merged to 0 or that we'd need to remove entries
    # 3 and 7 to set the nth bit of the merged entry to set the nth bit to 1.
    #
    # NOTE:
    #   The boolean part of the pair indicates which value needs to be removed
    #   (True -> remove all 1s and Xs; False -> remove all 0s and Xs). If all
    #   Xs and 1s in a given bit position are removed from a merge then the
    #   merged entry is guaranteed to have a 0 in the bit position. Vice-versa
    #   removing all Xs and 0s in a given bit position from a merge will result
    #   in a merged entry with a 1 in that position.
    #
    # As we want to make our merges as large as possible we select the smallest
    # set of entries to remove from the merge from ``options``.
    #
    # The whole process is then repeated since:
    #   * we ignored covered entries with more ``settable`` bits there may
    #     still be covered entries below the merged entry
    #   * after removing entries from the merge the merged entry is of lower
    #     generality and is therefore nearer the top of the table so new
    #     entries may be have become covered

    # Set of bit positions
    all_bits = tuple(1 << i for i in range(32))

    # While the merge is still worth considering continue to perform the
    # down-check.
    while merge.goodness > min_goodness:
        covered = list(_get_covered_keys_and_masks(merge, aliases))

        # If there are no covered entries (the merge is valid) then break out
        # of the loop.
        if not covered:
            break

        # For each covered entry work out which bits in the key-mask pair which
        # are not Xs are not covered by Xs in the merge key-mask pair. Only
        # keep track of the entries which have the fewest bits that we could
        # set.
        most_stringent = 33  # Not at all stringent
        bits_and_vals = set()
        for key, mask in covered:
            # Get the bit positions where there ISN'T an X in the covered entry
            # but there IS an X in the merged entry.
            settable = mask & ~merge.mask

            # Count the number of settable bits, if this is a more stringent
            # constraint than the previous constraint then ensure that we
            # record the new stringency and store which bits we need to set to
            # meet the constraint.
            n_settable = sum(1 for bit in all_bits if bit & settable)
            if n_settable <= most_stringent:
                if n_settable < most_stringent:
                    most_stringent = n_settable
                    bits_and_vals = set()

                # Add this settable mask and the required values to the
                # settables list.
                bits_and_vals.update((bit, not (key & bit)) for bit in
                                     all_bits if bit & settable)

        if most_stringent == 0:
            # If are there any instances where we could not possibly change a
            # bit to avoid aliasing an entry we'll return an empty merge and
            # give up.
            merge = _Merge(merge.routing_table, set())
            break
        else:
            # Get the smallest number of entries to remove to modify the
            # resultant key-mask to avoid covering a lower entry. Prefer to
            # modify more significant bits of the key mask.
            remove = set()  # Entries to remove
            for bit, val in sorted(bits_and_vals, reverse=True):
                working_remove = set()  # Holder for working remove set

                for i in merge.entries:
                    entry = merge.routing_table[i]

                    if ((not entry.mask & bit) or
                            (bool(entry.key & bit) is (not val))):
                        # If the entry has an X in this position then it will
                        # need to be removed regardless of whether we want to
                        # set a 0 or a 1 in this position, likewise it will
                        # need to be removed if it is a 0 and we want a 1 or
                        # vice-versa.
                        working_remove.add(i)

                # If the current remove set is empty or the new remove set is
                # smaller update the remove set.
                if not remove or len(working_remove) < len(remove):
                    remove = working_remove

            # Remove the selected entries from the merge
            merge = _Merge(merge.routing_table, merge.entries - remove)
    else:
        # NOTE: If there are no covered entries, that is, if the merge is
        # better than min goodness AND valid this `else` clause is not reached.
        # Ensure than an empty merge is returned if the above loop was aborted
        # early with a non-empty merge.
        merge = _Merge(merge.routing_table, set())

    return merge


def _get_covered_keys_and_masks(merge, aliases):
    """Get keys and masks which would be covered by the entry resulting from
    the merge.

    Parameters
    ----------
    aliases : {(key, mask): {(key, mask), ...}, ...}
        Map of key-mask pairs to the sets of key-mask pairs that they actually
        represent.

    Yields
    ------
    (key, mask)
        Pairs of keys and masks which would be covered if the given `merge`
        were to be applied to the routing table.
    """
    # For every entry in the table below the insertion index see which keys
    # and masks would overlap with the key and mask of the merged entry.
    for entry in merge.routing_table[merge.insertion_index:]:
        key_mask = (entry.key, entry.mask)
        keys_masks = aliases.get(key_mask, [key_mask])

        for key, mask in keys_masks:
            if intersect(merge.key, merge.mask, key, mask):
                yield key, mask
