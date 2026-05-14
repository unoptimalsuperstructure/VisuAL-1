import numpy as np
from abc import ABC, abstractmethod

class MatrixOperation(ABC):
    def __init__(self, request: dict):
        self.matrix = request.get('matrix')
        self.verify()
        self.A = np.array(self.matrix)

    def verify(self):
        if not self.matrix:
            print("Error: Missing matrix")
            raise ValueError("Missing matrix")
        check = np.array(self.matrix, dtype = object)
        if check.ndim == 1 and len(check) > 1:
            print("Error: Inhomogeneous row lengths are not allowed")   
            raise ValueError("Inhomogeneous row lengths are not allowed")        
        if check.ndim not in (2, 3):
            print("Error: Input must be a 2 or 3-dimensional matrix")
            raise ValueError("Input must be a 2 or 3-dimensional matrix")

    @abstractmethod
    def execute(self):
        pass

class SVDOperation(MatrixOperation):
    def execute(self):
        U, S, Vt = np.linalg.svd(self.A)
        return {
            "matrix": self.matrix,
            "U": U.tolist(),
            "S": S.tolist(),
            "Vt": Vt.tolist()
        }

class PCAOperation(MatrixOperation):
    def __init__(self, request: dict):
        super().__init__(request)
        self.norm = request.get('norm', True)

    def execute(self):
            original_shape = self.A.shape
            is_3d = (self.A.ndim == 3)

            if is_3d:
                n_slices, _, _ = self.A.shape
                A_flat = self.A.reshape(n_slices, -1)  
            else:
                A_flat = self.A

            mean = np.mean(A_flat, axis=0)
            A_centered = A_flat - mean

            if self.norm:
                std = np.std(A_centered, axis=0, ddof=1)
                std[std == 0] = 1
                A_centered = A_centered / std

            cov = np.cov(A_centered, rowvar=False)

            eigenvalues, eigenvectors = np.linalg.eigh(cov)

            idx = np.argsort(eigenvalues)[::-1]
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]

            scores = A_centered @ eigenvectors

            explained_ratio = eigenvalues / np.sum(eigenvalues)

            full_reconstruction = scores @ eigenvectors.T

            layers = []
            reconstruction_flat = full_reconstruction.copy()

            # Removal of each PC and reconstructing the data

            for i in range(len(eigenvalues)):
                layer_flat = np.outer(scores[:, i], eigenvectors[:, i].T)
                reconstruction_flat -= layer_flat

                layer = layer_flat.reshape(original_shape) if is_3d else layer_flat
                reconstruction = reconstruction_flat.reshape(original_shape) if is_3d else reconstruction_flat

                # Note: might choose to delete some of the redundant keys in the dict

                layers.append({
                    'pc_index': i,
                    'direction': eigenvectors[:, i].tolist(),
                    'scores': scores[:, i].tolist(),
                    'eigenvalue': float(eigenvalues[i]),
                    'explained_ratio': float(explained_ratio[i]),
                    'cumulative_ratio': float(np.sum(explained_ratio[:i+1])),
                    'removed_contribution': layer.tolist(),
                    'reconstruction': (reconstruction + np.mean(A_flat, axis=0).reshape(original_shape[1:] if is_3d else mean.shape)).tolist() 
                })

            return {
                'original': self.A.tolist(),
                'original_shape': list(original_shape),
                'is_3d': is_3d,
                'mean': mean.tolist(),
                'covariance': cov.tolist(),
                'layers': layers
            }

class MatrixEngine:
    operations = {
        'svd': SVDOperation,
        'pca': PCAOperation
    }

    @classmethod
    def run(cls, request: dict):
        operation_type = request.get('operation')
        operation_class = cls.operations.get(operation_type)

        if not operation_class:
            return "Error, Unsupported operation"
        
        operation_instance = operation_class(request)
        return operation_instance.execute()

test = {
    "operation": "pca",
    "matrix": [[2.5, 2], [0.5, 0.7], [2.2, 2.9], [1.9, 2.2], [3.1, 3.0], [2.3, 2.7], [2, 1.6], [1, 1.1], [1.5, 1.6], [1.1, 0.9]],
    "norm": True
    }

print(MatrixEngine.run(test))

# def run_svd(matrix: list) -> dict:
#     '''Returns the initial matrix and SVD decomposed matrix'''
#     U, S, Vt = np.linalg.svd(np.array(matrix))
#     return {
#         "matrix": matrix,
#         "U": U.tolist(),
#         "S": S.tolist(), 
#         "Vt": Vt.tolist()
#     }

# def run_pca(matrix_data: list, norm: bool = True) -> dict:
#     '''Returns the intial matrix, PC, data after removal of PC,...'''
#     A = np.array(matrix_data)

#     if A.ndim not in (2, 3):
#         return "Error: Input must be a 2 or 3-dimensional matrix"

#     original_shape = A.shape
#     is_3d = (A.ndim == 3)

#     if is_3d:
#         n_slices, _, _ = A.shape
#         A_flat = A.reshape(n_slices, -1)  
#     else:
#         A_flat = A

#     mean = np.mean(A_flat, axis=0)
#     A_centered = A_flat - mean

#     if norm:
#         std = np.std(A_centered, axis=0, ddof=1)
#         std[std == 0] = 1
#         A_centered = A_centered / std

#     cov = np.cov(A_centered, rowvar=False)

#     eigenvalues, eigenvectors = np.linalg.eigh(cov)

#     idx = np.argsort(eigenvalues)[::-1]
#     eigenvalues = eigenvalues[idx]
#     eigenvectors = eigenvectors[:, idx]

#     scores = A_centered @ eigenvectors

#     explained_ratio = eigenvalues / np.sum(eigenvalues)

#     full_reconstruction = scores @ eigenvectors.T

#     layers = []
#     reconstruction_flat = full_reconstruction.copy()

#     # Removal of each PC and reconstructing the data

#     for i in range(len(eigenvalues)):
#         layer_flat = np.outer(scores[:, i], eigenvectors[:, i].T)
#         reconstruction_flat -= layer_flat

#         layer = layer_flat.reshape(original_shape) if is_3d else layer_flat
#         reconstruction = reconstruction_flat.reshape(original_shape) if is_3d else reconstruction_flat

#         # Note: might choose to delete some of the keys in the dict

#         layers.append({
#             'pc_index': i,
#             'direction': eigenvectors[:, i].tolist(),
#             'scores': scores[:, i].tolist(),
#             'eigenvalue': float(eigenvalues[i]),
#             'explained_ratio': float(explained_ratio[i]),
#             'cumulative_ratio': float(np.sum(explained_ratio[:i+1])),
#             'removed_contribution': layer.tolist(),
#             'reconstruction': (reconstruction + np.mean(A_flat, axis=0).reshape(original_shape[1:] if is_3d else mean.shape)).tolist() 
#         })

#     return {
#         'original': A.tolist(),
#         'original_shape': list(original_shape),
#         'is_3d': is_3d,
#         'mean': mean.tolist(),
#         'covariance': cov.tolist(),
#         'layers': layers
#     }