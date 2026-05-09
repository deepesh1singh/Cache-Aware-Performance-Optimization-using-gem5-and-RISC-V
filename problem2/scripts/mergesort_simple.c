/*
 * Simple In-Memory Merge Sort
 * Reads 10MB of random integers from binary file and sorts them in memory
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define NUM_ELEMENTS (10 * 1024 * 1024 / sizeof(int32_t))  // 10MB / 4 bytes = 2.5M integers

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

int main() {
    int32_t *data = NULL;
    int32_t *temp = NULL;
    FILE *fp = NULL;
    size_t elements_read;
    
    printf("Simple Merge Sort - Starting\n");
    printf("Allocating memory for %lu integers (%lu MB)\n", 
           (unsigned long)NUM_ELEMENTS, 
           (unsigned long)(NUM_ELEMENTS * sizeof(int32_t) / (1024 * 1024)));
    
    // Allocate memory
    data = (int32_t *)malloc(NUM_ELEMENTS * sizeof(int32_t));
    temp = (int32_t *)malloc(NUM_ELEMENTS * sizeof(int32_t));
    
    if (!data || !temp) {
        fprintf(stderr, "Memory allocation failed\n");
        free(data);
        free(temp);
        return 1;
    }
    
    // Read data from binary file
    printf("Reading random numbers from file...\n");
    fp = fopen("/workspace/problem2/random_numbers.bin", "rb");
    if (!fp) {
        fprintf(stderr, "Failed to open /workspace/problem2/random_numbers.bin\n");
        free(data);
        free(temp);
        return 1;
    }
    
    elements_read = fread(data, sizeof(int32_t), NUM_ELEMENTS, fp);
    fclose(fp);
    
    if (elements_read != NUM_ELEMENTS) {
        fprintf(stderr, "Warning: Read %lu elements instead of %lu\n", 
                (unsigned long)elements_read, (unsigned long)NUM_ELEMENTS);
    }
    
    printf("Starting merge sort on %lu elements...\n", (unsigned long)elements_read);
    
    // Perform merge sort
    merge_sort(data, temp, 0, elements_read - 1);
    
    printf("Merge sort completed!\n");
    
    // Verify sorted (check first 10 and last 10)
    printf("First 10 sorted values: ");
    for (int i = 0; i < 10 && i < elements_read; i++) {
        printf("%d ", data[i]);
    }
    printf("\n");
    
    printf("Last 10 sorted values: ");
    for (int i = elements_read - 10; i < elements_read; i++) {
        printf("%d ", data[i]);
    }
    printf("\n");
    
    // Cleanup
    free(data);
    free(temp);
    
    printf("Simple Merge Sort - Completed Successfully\n");
    return 0;
}
