/* Aliases are built using a trie structure as this avoids the need for
 * rebalancing at the cost of more memory.
 */
#include "platform.h"
#include "routing_table.h"
#include <stdio.h>


#ifndef __ALIASES_H__

/*****************************************************************************/
/* Vector-like object ********************************************************/


typedef struct _alias_element_t{  // Element of an alias list
    key_mask_t key_mask;  // key_mask of the element
    uint32_t source;    // Source of packets matching the element
} alias_element_t;


typedef struct _alias_list_t{
    // Linked list of arrays
    unsigned int n_elements;     // Elements in this instance
    unsigned int max_size;       // Max number of elements in this instance
    struct _alias_list_t *next;  // Next element in list of lists
    alias_element_t data;        // Data region
} alias_list_t;


// Create a new list on the stack
static inline alias_list_t* alias_list_new(unsigned int max_size){
    // Compute how much memory to allocate
    unsigned int size =
        sizeof(alias_list_t) + (max_size - 1)*sizeof(alias_element_t);

    // Allocate and then fill in values
    alias_list_t *as = MALLOC(size);
    as->n_elements = 0;
    as->max_size = max_size;
    as->next = NULL;

    return as;
}


// Append an element to a list
static inline bool alias_list_append(
        alias_list_t *as, key_mask_t val, uint32_t source){
    if (as->n_elements < as->max_size){

        (&as->data)[as->n_elements].key_mask = val;
        (&as->data)[as->n_elements].source = source;
        as->n_elements++;
        return true;
    }
    else{
        // Cannot append!
        return false;
    }
}


// Get an element from the list
static inline alias_element_t alias_list_get(alias_list_t *as, unsigned int i){
    return (&as->data)[i];
}


// Append a list to an existing list
static inline void alias_list_join(alias_list_t *a, alias_list_t *b){
    // Traverse the list elements until we reach the end.
    while (a->next != NULL){
        a = a->next;
    }

    // Store the next element
    a->next = b;
}


// Delete all elements in an alias list
static inline void alias_list_delete(alias_list_t *a){
    if (a->next != NULL){
        alias_list_delete(a->next);
        a->next = NULL;
    }
    FREE(a);
}


/*****************************************************************************/


/*****************************************************************************/
/* Map-like object ***********************************************************/
// Implemented as an AA tree


typedef union _key_t {key_mask_t km; int64_t as_int;} a_key_t;

typedef struct _node_t{
    // Key and value of this node
    a_key_t key;
    alias_list_t *val;

    unsigned int level;

    // Children
    struct _node_t *left, *right;
} node_t;

typedef struct _aliases_t{
    node_t *root;
} aliases_t;


// Create a new, empty, aliases container
static inline aliases_t aliases_init(void){
    aliases_t aliases = {NULL};
    return aliases;
}


static inline node_t* _aliases_find_node(node_t *node, a_key_t key){
    while (node != NULL){
        if (key.as_int == node->key.as_int){
            // This is the requested item, return it
            return node;
        }
        else if (key.as_int < node->key.as_int){
            // Go left
            node = node->left;
        }
        else{
            // Go right
            node = node->right;
        }
    }
    return NULL;  // We didn't find the requested item
}


// Retrieve an element from an aliases container
static inline alias_list_t* aliases_find(aliases_t *a, key_mask_t key){
    // Search the tree
    node_t *node = _aliases_find_node(a->root, (a_key_t) key);
    if (node == NULL){
        return NULL;
    }
    else{
        return node->val;
    }
}


// See if the aliases contain holds an element
static inline bool aliases_contains(aliases_t *a, key_mask_t key){
    return aliases_find(a, key) != NULL;
}


static inline node_t* _aliases_skew(node_t *n){
    if (n == NULL){
        return NULL;
    }
    else if (n->left == NULL){
        return n;
    }
    else if (n->level == n->left->level){
        node_t *node_pointer = n->left;
        n->left = node_pointer->right;
        node_pointer->right = n;
        return node_pointer;
    }
    else{
        return n;
    }
}


static inline node_t* _aliases_split(node_t *n){
    if (n == NULL){
      return NULL;
    }
    else if (n->right == NULL || n->right->right == NULL){
        return n;
    }
    else if (n->level == n->right->right->level){
        node_t *r = n->right;
        n->right = r->left;
        r->left = n;
        r->level++;
        return r;
    }
    else{
        return n;
    }
}


static inline node_t* _aliases_insert(
        node_t *n, a_key_t key, alias_list_t *val){
    if (n == NULL){
        // If the node is NULL then create a new Node
        // Malloc room for the node
        node_t *n = MALLOC(sizeof(node_t));

        // Assign the values
        n->key = key;
        n->val = val;
        n->left = n->right = NULL;
        n->level = 1;

        return n;
    }
    else if (key.as_int < n->key.as_int){
        // Go left
        n->left = _aliases_insert(n->left, key, val);
    }
    else if (key.as_int > n->key.as_int){
        // Go right
        n->right = _aliases_insert(n->right, key, val);
    }
    else{
        // Replace the value
        n->val = val;
    }

    // Rebalance the tree
    n = _aliases_skew(n);
    n = _aliases_split(n);

    return n;
}


// Add/overwrite an element into an aliases tree
static inline void aliases_insert(
        aliases_t *a, key_mask_t key, alias_list_t *value){
    // Insert into, and balance, the tree
    a->root = _aliases_insert(a->root, (a_key_t) key, value);
}


// Remove an element from an aliases tree
static inline void aliases_remove(aliases_t *a, key_mask_t key){
    // XXX This is a hack which removes the reference to the element in the
    // tree but doesn't remove the Node from the tree.
    node_t *n = _aliases_find_node(a->root, (a_key_t) key);
    if (n != NULL){
        n->val = NULL;
    }
}


static inline void _aliases_clear(node_t *n){
    if (n == NULL){
        return;
    }

    // Remove any children
    if (n->left != NULL){
        _aliases_clear(n->left);
    }

    if (n->right != NULL){
        _aliases_clear(n->right);
    }

    // Clear the value
    if (n->val != NULL){
        alias_list_delete(n->val);
    }

    // Remove self
    FREE(n);
}


// Remove all elements from an aliases container and free all sub-containers
static inline void aliases_clear(aliases_t *a){
    _aliases_clear(a->root);
}

/*****************************************************************************/

#define __ALIASES_H__
#endif  // __ALIASES_H__
