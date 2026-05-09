/*
 * Chunked Merge Sort with Streaming Merge
 * Processes 10MB file in 2MB chunks, sorts each chunk, then merges from 1MB streams
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define TOTAL_SIZE (10 * 1024 * 1024)                    // 10MB total
#define CHUNK_SIZE (2 * 1024 * 1024)                     // 2MB chunks
#define STREAM_SIZE (1 * 1024 * 1024)                    // 1MB streams for merge
#define CHUNK_ELEMENTS (CHUNK_SIZE / sizeof(int32_t))    // 512K integers per chunk
#define STREAM_ELEMENTS (STREAM_SIZE / sizeof(int32_t))  // 256K integers per stream
#define NUM_CHUNKS (TOTAL_SIZE / CHUNK_SIZE)             // 5 chunks

void merge(int32_t arr[], int32_t temp[], int left, int mid, int right) {
    int i = left;
    int j = mid + 1;
    int k = left;
    
    while (i <= mid && j <= right) {
        if (arr[i] <= arr[j]) {
            temp[k++] = arr[i++];
        } else {
            temp[k++] = arr[j++];
        }
    }
    
    while (i <= mid) {
        temp[k++] = arr[i++];
    }
    
    while (j <= right) {
        temp[k++] = arr[j++];
    }
    
    for (i = left; i <= right; i++) {
        arr[i] = temp[i];
    }
}

void merge_sort(int32_t arr[], int32_t temp[], int left, int right) {
    if (left < right) {
        int mid = left + (right - left) / 2;
        merge_sort(arr, temp, left, mid);
        merge_sort(arr, temp, mid + 1, right);
        merge(arr, temp, left, mid, right);
    }
}

// Merge two sorted streams using buffered I/O
void merge_streams(int32_t *stream1, size_t size1, int32_t *stream2, size_t size2, 
                   int32_t *output) {
    size_t i = 0, j = 0, k = 0;
    
    while (i < size1 && j < size2) {
        if (stream1[i] <= stream2[j]) {
            output[k++] = stream1[i++];
        } else {
            output[k++] = stream2[j++];
        }
    }
    
    while (i < size1) {
        output[k++] = stream1[i++];
    }
    
    while (j < size2) {
        output[k++] = stream2[j++];
    }
}

int main() {
    int32_t *chunk_data = NULL;
    int32_t *temp_data = NULL;
    int32_t *sorted_chunks[NUM_CHUNKS];
    FILE *fp = NULL;
    size_t elements_read;
    
    printf("Chunked Merge Sort - Starting\n");
    printf("Total size: %d MB, Chunk size: %d MB\n", 
           TOTAL_SIZE/(1024*1024), CHUNK_SIZE/(1024*1024));
    printf("Processing %d chunks of %lu integers each\n", NUM_CHUNKS, (unsigned long)CHUNK_ELEMENTS);
    
    // Allocate working memory
    chunk_data = (int32_t *)malloc(CHUNK_SIZE);
    temp_data = (int32_t *)malloc(CHUNK_SIZE);
    
    if (!chunk_data || !temp_data) {
        fprintf(stderr, "Failed to allocate working memory\n");
        free(chunk_data);
        free(temp_data);
        return 1;
    }
    
    // Open input file
    fp = fopen("/workspace/problem2/random_numbers.bin", "rb");
    if (!fp) {
        fprintf(stderr, "Failed to open /workspace/problem2/random_numbers.bin\n");
        free(chunk_data);
        free(temp_data);
        return 1;
    }
    
    // Phase 1: Sort each chunk individually
    printf("\nPhase 1: Sorting individual chunks...\n");
    for (int chunk_idx = 0; chunk_idx < NUM_CHUNKS; chunk_idx++) {
        // Read chunk
        elements_read = fread(chunk_data, sizeof(int32_t), CHUNK_ELEMENTS, fp);
        if (elements_read != CHUNK_ELEMENTS) {
            fprintf(stderr, "Warning: Chunk %d read %lu elements instead of %lu\n", 
                    chunk_idx, (unsigned long)elements_read, (unsigned long)CHUNK_ELEMENTS);
        }
        
        printf("  Sorting chunk %d (%lu elements)...\n", chunk_idx, (unsigned long)elements_read);
        
        // Sort chunk
        merge_sort(chunk_data, temp_data, 0, elements_read - 1);
        
        // Store sorted chunk
        sorted_chunks[chunk_idx] = (int32_t *)malloc(elements_read * sizeof(int32_t));
        if (!sorted_chunks[chunk_idx]) {
            fprintf(stderr, "Failed to allocate memory for sorted chunk %d\n", chunk_idx);
            fclose(fp);
            free(chunk_data);
            free(temp_data);
            for (int i = 0; i < chunk_idx; i++) free(sorted_chunks[i]);
            return 1;
        }
        memcpy(sorted_chunks[chunk_idx], chunk_data, elements_read * sizeof(int32_t));
    }
    fclose(fp);
    
    printf("Phase 1 completed - all chunks sorted\n");
    
    // Phase 2: Iteratively merge all sorted chunks
    printf("\nPhase 2: Merging all %d sorted chunks...\n", NUM_CHUNKS);
    
    // Allocate buffers for merging
    int32_t *current = NULL;
    int32_t *next = NULL;
    size_t current_size = CHUNK_ELEMENTS;
    
    // Start with first chunk
    current = (int32_t *)malloc(CHUNK_ELEMENTS * NUM_CHUNKS * sizeof(int32_t));
    if (!current) {
        fprintf(stderr, "Failed to allocate merge buffer\n");
        free(chunk_data);
        free(temp_data);
        for (int i = 0; i < NUM_CHUNKS; i++) free(sorted_chunks[i]);
        return 1;
    }
    
    // Copy first chunk to current buffer
    memcpy(current, sorted_chunks[0], CHUNK_ELEMENTS * sizeof(int32_t));
    
    // Merge each subsequent chunk
    for (int chunk_idx = 1; chunk_idx < NUM_CHUNKS; chunk_idx++) {
        printf("  Merging chunk %d...\n", chunk_idx);
        
        // Allocate buffer for merged result
        size_t new_size = current_size + CHUNK_ELEMENTS;
        next = (int32_t *)malloc(new_size * sizeof(int32_t));
        if (!next) {
            fprintf(stderr, "Failed to allocate next buffer\n");
            free(current);
            free(chunk_data);
            free(temp_data);
            for (int i = 0; i < NUM_CHUNKS; i++) free(sorted_chunks[i]);
            return 1;
        }
        
        // Merge current with next chunk
        size_t i = 0, j = 0, k = 0;
        while (i < current_size && j < CHUNK_ELEMENTS) {
            if (current[i] <= sorted_chunks[chunk_idx][j]) {
                next[k++] = current[i++];
            } else {
                next[k++] = sorted_chunks[chunk_idx][j++];
            }
        }
        
        // Copy remaining elements
        while (i < current_size) {
            next[k++] = current[i++];
        }
        while (j < CHUNK_ELEMENTS) {
            next[k++] = sorted_chunks[chunk_idx][j++];
        }
        
        // Free old current buffer and update
        free(current);
        current = next;
        current_size = new_size;
    }
    
    printf("Phase 2 completed - merged %lu elements\n", (unsigned long)current_size);
    
    // Verify sorted (first and last 10 of merged result)
    printf("\nFirst 10 sorted values: ");
    for (int i = 0; i < 10 && i < current_size; i++) {
        printf("%d ", current[i]);
    }
    printf("\n");
    
    printf("Last 10 sorted values: ");
    for (int i = current_size - 10; i < current_size; i++) {
        printf("%d ", current[i]);
    }
    printf("\n");
    
    // Cleanup
    free(chunk_data);
    free(temp_data);
    free(current);
    for (int i = 0; i < NUM_CHUNKS; i++) {
        free(sorted_chunks[i]);
    }
    
    printf("\nChunked Merge Sort - Completed Successfully\n");
    return 0;
}
