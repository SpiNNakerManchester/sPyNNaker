//#include <debug.h>

#ifndef __PLATFORM_H__

    //! a extra heap, that exploits sdram which can be easily regenerated.
    heap_t * stolen_sdram_heap = NULL;

    //! \brief builds a new heap based off stolen sdram blocks from cores
    //! synaptic matrix's. Needs to merge in the true sdram free heap, as
    //! otherwise its impossible to free the block properly.
    //! \param[in] sizes_region; the sdram address where the free regions exist
    //! \return None
    static inline void platform_new_heap_creation(address_t sizes_region){
        // TODO hook removal here if we decide on this insanity
        stolen_sdram_heap = sv->sdram_heap;
        /*
        // set up states
        heap_t *stolen_sdram_heap = (heap_t *) base;
        uint read_position = 0;
        uint x_blocks = sizes_region[read_position];
        uint size_free = 0;
        read_position += 1;

        // set the first and last to match sdram heap
        stolen_sdram_heap->first = sark_xalloc(sark.heap, sizeof(block_t), 0, 0)
        stolen_sdram_heap->first->next = sv->sdram_heap->first->next;
        stolen_sdram_heap->last = sark_xalloc(sark.heap, sizeof(block_t), 0, 0)
        stolen_sdram_heap->last->next = sv->sdram_heap->last->next;


        // read first points
        address_t address = sizes_region[read_position];
        uint size = sizes_region[read_position + 1];
        read_position += 2;

        //TODO HAVE NO IDEA HOW YOUR MEANT TO MAKE THIS HEAP!!!!!!!!
        // iterate through the data creating blocks
        for (uint current_block = 0; current_block < x_blocks - 1;
                current_block++){

            // read next block, to figure frees
            address_t next_address = sizes_region[read_position];
            uint next_size = sizes_region[read_position + 1];
            read_position += 2;

            // create the next block
            block_t *block = sark_xalloc(sark.heap, sizeof(block_t), 0, 0)
            block->free = next_address;
            block->next = address + size;
            size_free += size;




        }

        block_t *first = (block_t *) stolen_sdram_heap->buffer;
        block_t *last = (block_t *) ((uchar *) top - sizeof(block_t));

        stolen_sdram_heap->free = stolen_sdram_heap->first = first;
        stolen_sdram_heap->last = first->next = last;
        stolen_sdram_heap->free_bytes = (uchar *) last - (uchar *) first - sizeof(block_t);

        last->next = NULL;
        first->free = NULL;

        last->free = NULL;	// Not really necessary*/
    }

    //! \brief resets the heap so that it looks like it was before
    static inline void platform_kill_fake_heap(){
        return;
    }

    //! \brief allows a search of the 2 heaps available. (DTCM, stolen SDRAM)
    //! \param[in] bytes: the number of bytes to allocate.
    //! \return: the address of the block of memory to utilise.
    static inline void * safe_malloc(uint bytes){

        // try DTCM
        void* p = sark_xalloc(sark.heap, bytes, 0, 0);
        if (p != NULL){
            return p;
        }

        // try SDRAM stolen from the cores synaptic matrix areas.
        p = sark_xalloc(stolen_sdram_heap, bytes, 0, ALLOC_LOCK);

        if (p == NULL){
            //log_error("Failed to malloc %u bytes.\n", bytes);
        }
        return p;
    }

    //! \brief locates the biggest block of available memory from the heaps
    //! \return the biggest block size in the heaps.
    static inline uint platform_max_available_block_size(){
        uint max_dtcm_block = sark_heap_max(sark.heap, ALLOC_LOCK);
        uint max_sdram_block = sark_heap_max(stolen_sdram_heap, ALLOC_LOCK);
        return max(max_dtcm_block, max_sdram_block);
        //if (max_dtcm_block > max_sdram_block){
        //    return max_dtcm_block;
        //}
        //else{
        //    return max_sdram_block;
        //}
    }

    //! \brief frees the sdram allcoated from whatever heap it came from
    static inline void safe_x_free(void *ptr){
        if ((int) ptr >= DTCM_BASE && (int) ptr <= DTCM_TOP) {
            sark_xfree(sark.heap, ptr, 0);
        } else {
            sark_xfree(stolen_sdram_heap, ptr, ALLOC_LOCK);
        }
    }

    #ifdef PROFILED
        void profile_init();
        void *profiled_malloc(uint bytes);
        void profiled_free(void * ptr);

        #define MALLOC profiled_malloc
        #define FREE   profiled_free
        #else
        #define MALLOC safe_malloc
        #define FREE   safe_x_free
    #endif

#define __PLATFORM_H__
#endif  // __PLATFORM_H__
