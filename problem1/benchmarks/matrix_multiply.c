/*
 * Matrix Multiply Benchmark for RISCV
 * 
 * This benchmark performs square matrix multiplication to stress
 * the memory subsystem and cache hierarchy.
 * 
 * Compile for RISCV:
 *   riscv64-unknown-linux-gnu-gcc -O2 -static matrix_multiply.c -o matrix_multiply
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MATRIX_SIZE 256  /* Configurable: 64, 128, 256 */

volatile int A[MATRIX_SIZE][MATRIX_SIZE];
volatile int B[MATRIX_SIZE][MATRIX_SIZE];
volatile int C[MATRIX_SIZE][MATRIX_SIZE];

void matrix_init() {
    int i, j;
    /* Initialize A and B with simple values */
    for (i = 0; i < MATRIX_SIZE; i++) {
        for (j = 0; j < MATRIX_SIZE; j++) {
            A[i][j] = (i * MATRIX_SIZE + j) % 100;
            B[i][j] = (j * MATRIX_SIZE + i) % 100;
            C[i][j] = 0;
        }
    }
}

void matrix_multiply() {
    int i, j, k;
    int sum;
    
    /* Classic O(n^3) matrix multiply */
    for (i = 0; i < MATRIX_SIZE; i++) {
        for (j = 0; j < MATRIX_SIZE; j++) {
            sum = 0;
            for (k = 0; k < MATRIX_SIZE; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}

void matrix_verify() {
    /* Simple verification: check a few values */
    printf("C[0][0] = %d\n", C[0][0]);
    printf("C[%d][%d] = %d\n", MATRIX_SIZE-1, MATRIX_SIZE-1, C[MATRIX_SIZE-1][MATRIX_SIZE-1]);
}

int main() {
    printf("Matrix Multiply Benchmark (RISCV)\n");
    printf("Matrix Size: %dx%d\n", MATRIX_SIZE, MATRIX_SIZE);
    
    printf("Initializing matrices...\n");
    matrix_init();
    
    printf("Starting matrix multiplication...\n");
    matrix_multiply();
    
    printf("Verifying results...\n");
    matrix_verify();
    
    printf("Benchmark complete!\n");
    return 0;
}
