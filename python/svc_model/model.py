"""
-------------------------------------------------------
[Program Description]
-------------------------------------------------------
Author:  einsteinoyewole
Email:   eo2233@nyu.edu
__updated__ = "3/2/25"
-------------------------------------------------------
"""

# Imports
from typing import Dict

import pandas as pd
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.svm import SVC
import numpy as np

# Constants
SEED = 4
svc_model = SVC(max_iter=10, probability=True, random_state=SEED)
data, Z_grid = None, None


def get_iris_data():
    """
    -------------------------------------------------------
    Returns the iris dataset in 3D space for visualization.
    -------------------------------------------------------
    Returns:
       [return value name - return value description (return value type)]
    -------------------------------------------------------
    """
    iris = load_iris()
    X, y = iris.data, iris.target

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Apply PCA
    pca = PCA(n_components=3)
    pca.set_output(transform="pandas")
    X_pca = pca.fit_transform(X_scaled)

    # Scale PCA components to [0, 1]
    mscaler = MinMaxScaler(feature_range=(0, 0.5))
    mscaler.set_output(transform="pandas")
    X_pca = mscaler.fit_transform(X_pca)

    pca_data = X_pca.copy().rename(columns={'pca0': 'x', 'pca1': 'y', 'pca2': 'z'})
    pca_data['target'] = y

    return pca_data


def get_mesh_decision():
    """
    -------------------------------------------------------
    Returns the mesh grid for decision boundary visualization.
    -------------------------------------------------------
    Returns:
       Z_grid - The mesh grid for decision boundary visualization (DataFrame)
    -------------------------------------------------------
    """
    global data, Z_grid
    if Z_grid is not None:
        return Z_grid
    if data is None:
        data = get_iris_data()

    # Get the min and max values for each axis
    x_min, x_max = data['x'].min() - 0.1, data['x'].max() + 0.1
    y_min, y_max = data['y'].min() - 0.1, data['y'].max() + 0.1
    z_min, z_max = data['z'].min() - 0.1, data['z'].max() + 0.1
    # Create a mesh grid
    xx, yy, zz = np.meshgrid(np.arange(x_min, x_max, 0.05),
                             np.arange(y_min, y_max, 0.05),
                             np.arange(z_min, z_max, 0.05))

    # Flatten the mesh grid and concatenate the coordinates on the last axis
    Z_data = np.c_[xx.ravel(), yy.ravel(), zz.ravel()]
    Z_grid = pd.DataFrame(Z_data, columns=['x', 'y', 'z'])  # Create a DataFrame
    Z_grid['pred'] = None  # Initialize target column with None
    Z_grid.reset_index(inplace=True)  # Reset index
    print(Z_grid.shape)
    return Z_grid


def train_svc(max_iter: int, C: float = None, kernel: str = None, degree: int = None, gamma: str = None, tol: float = None):
    """
    -------------------------------------------------------
    Trains the SVC model with the provided parameters. If no
    -------------------------------------------------------
    Parameters:
         C - Regularization parameter (float)
         kernel - Specifies the kernel type to be used in the algorithm (str)
         degree - Degree of the polynomial kernel function (int)
         gamma - Kernel coefficient for 'rbf', 'poly' and 'sigmoid' (str)
         tol - Tolerance for stopping criterion (float)
         max_iter - Hard limit on iterations within solver, or -1 for no limit (int)
    """
    global svc_model, data, Z_grid
    # Get the iris dataset
    if data is None:
        data = get_iris_data()
    y = data['target']
    X = data.drop(columns=['target'])

    # Set the parameters for the SVC model
    new_max_iter = max_iter + svc_model.n_iter_[0] if hasattr(svc_model, "n_iter_") else 0
    params = {
        'C': C,
        'kernel': kernel,
        'degree': degree,
        'gamma': gamma,
        'tol': tol,
        'max_iter': new_max_iter
    }
    params = {k: v for k, v in params.items() if v is not None}
    svc_model.set_params(**params)

    # Train the SVC model
    svc_model.fit(X, y)

    # Predict the target for the mesh grid
    if Z_grid is None:
        Z_grid = get_mesh_decision()

    old_grid = Z_grid.copy()
    Z_grid['pred'] = svc_model.predict(old_grid[['x', 'y', 'z']])
    set_diff = Z_grid[Z_grid['pred'] != old_grid['pred']]
    print(f"for iteration {svc_model.n_iter_} # of updates", set_diff.shape)

    return {
        'decision_boundary': Z_grid,  # set_diff,
        'support_vectors': svc_model.support_vectors_.tolist(),
        'accuracy': svc_model.score(X, y),
        'converged': bool(svc_model.fit_status_),
        'reached_max_iter': all(svc_model.n_iter_ == new_max_iter)
    }


def reset(C: float = None, kernel: str = None, degree: int = None, gamma: str = None, tol: float = None,
          max_iter: int = 10):
    """
    -------------------------------------------------------
    Resets the SVC model and iris data and grid.
    -------------------------------------------------------
    """
    global svc_model, data, Z_grid
    params = {
        'C': C,
        'kernel': kernel,
        'degree': degree,
        'gamma': gamma,
        'tol': tol,
        'max_iter': max_iter
    }
    params = {k: v for k, v in params.items() if v is not None}
    svc_model = SVC(probability=True, **params)
    data, Z_grid = get_iris_data(), get_mesh_decision()

def svc_predict(X):
    """
    -------------------------------------------------------
    Predicts the target for the given data using the SVC model.
    -------------------------------------------------------
    Parameters:
        X - The data to predict (iterable)
    Returns:
        The predicted target (iterable)
    -------------------------------------------------------
    """
    return svc_model.predict(X)
