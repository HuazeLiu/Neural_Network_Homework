import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
#sns.set_style('white')

import tensorflow as tf
import tensorflow_datasets as tfds
import matplotlib.pyplot as plt
import numpy as np
import time
import tqdm.notebook as tqdm

def get_dataset(name):
    images, labels, label_names = None, None, list(map(str, range(10)))
    if name == 'ones_and_zeros':
        mnist = tfds.image_classification.MNIST()
        mnist.download_and_prepare()
        data = tfds.as_numpy(mnist.as_dataset(split='train', as_supervised=True).batch(5000))
        images, labels = next(iter(data))
        images, labels = images[labels <= 1][:, :, :, 0].astype(float) / 128 - 1., labels[labels <= 1].astype(float)
    if name == 'mnist':
        mnist = tfds.image_classification.MNIST()
        mnist.download_and_prepare()
        data = tfds.as_numpy(mnist.as_dataset(split='train', as_supervised=True).batch(5000))
        images, labels = next(iter(data))
        images, labels = images[:, :, :, 0].astype(float) / 128 - 1., labels.astype(int)
    elif name == 'horses_and_humans':
        hh = tfds.image_classification.HorsesOrHumans()
        hh.download_and_prepare()
        data = tfds.as_numpy(hh.as_dataset(split='train', as_supervised=True).map(lambda x, y: (tf.image.resize(
        tf.image.rgb_to_grayscale(x), (48, 48)), y)
        ).batch(100000))
        images, labels = next(iter(data))
        images, labels = images[labels <= 1][:, :, :, 0].astype(float) / 128 - 1., labels[labels <= 1].astype(float)
        label_names = ['horse', 'human']
    elif name == 'cats_and_dogs':
        cd = tfds.image_classification.CatsVsDogs()
        cd.download_and_prepare()
        data = tfds.as_numpy(cd.as_dataset(split='train', as_supervised=True).map(lambda x, y: (tf.image.resize(
        tf.image.rgb_to_grayscale(x), (64, 64)), y)
        ).batch(100000))
        images, labels = next(iter(data))
        images, labels = images[labels <= 1][:, :, :, 0].astype(float) / 128 - 1., labels[labels <= 1].astype(float)
        label_names = ['cat', 'dog']
    elif name == 'iris':
        import sklearn.datasets as datasets
        dataset = datasets.load_iris()
        features = dataset['data']
        targets = dataset['target']
        feature_names = dataset['feature_names']
        target_names = dataset['target_names']
        images, labels = features, targets 
        label_names = target_names

    f, subplots = plt.subplots(8, 8, figsize=(20, 20))
    i = 0
    for row in subplots:
        for subplot in row:
            subplot.imshow(images[i], cmap='gray')
            subplot.axis('off')
            i += 1
    plt.show()
    return images, labels, label_names


def gradient_descent(model, X, y, lr=1e-6, steps=2500, image_shape=None, watch=True):
    image_shape = image_shape if model.weights.ndim == 1 else None
    dims = np.array(image_shape).prod()

    losses = []
    progress = tqdm.trange(steps)
    if watch:
        from IPython import display
        f, ax = plt.subplots(X.shape[1] // dims, 3, figsize=(15,8))
        ax = np.atleast_2d(ax)

    for i in progress:
        loss, g = model.nll_and_grad(X, y)
        model.weights = model.weights - lr * g
        accuracy = model.accuracy(X, y)

        losses.append(loss)
        progress.set_description('Loss %.2f, accuracy: %.2f' % (loss, accuracy))

        # Plotting code
        if watch:
            [a.cla() for a in ax.flatten()]
            [a.axis('off') for a in ax.flatten()[1:]]
            display.clear_output(wait =True)
            
            ax[0, 0].plot(losses)
            if not (image_shape is None):
                ax[0, 1].imshow(model.weights[:dims].reshape(image_shape))
                ax[0, 2].imshow(g[:dims].reshape(image_shape))
                ax[0, 1].set_title('Loss: %.3f, accuracy: %.3f' % (loss, accuracy))

                for j in range(1, ax.shape[0]):
                    ax[j, 1].imshow(model.weights[(dims * j):(dims * (j+1))].reshape(image_shape))
                    ax[j, 2].imshow(g[(dims * j):(dims * (j+1))].reshape(image_shape))
                    ax[j, 0].imshow((X[0, (dims * j):(dims * (j+1))].reshape(image_shape)) )

            display.display(f)
            time.sleep(0.001)
        
    return losses


def test_split(X, y, Xtrain, ytrain, Xtest, ytest):
    assert Xtrain.shape[0] > 0.65 * X.shape[0] and Xtrain.shape[0] < 0.75 * X.shape[0], 'Xtrain should have 70% of the data'
    assert Xtest.shape[0] + Xtrain.shape[0] == X.shape[0], 'Xtrain and Xtest should include all the data'
    assert set(np.sum(Xtrain, axis=1)).isdisjoint(np.sum(Xtest, axis=1)), 'Xtrain and Xtest should not include the same observations'
    assert not np.all(np.concatenate([ytrain, ytest]) == y), 'Split should be randomized'
    assert not np.all(np.concatenate([ytest, ytrain]) == y), 'Split should be randomized'
    Xinds = np.argsort(X.sum(axis=1))
    Xttinds = np.argsort(np.concatenate([Xtrain, Xtest]).sum(axis=1))
    assert np.all(y[Xinds] == np.concatenate([ytrain, ytest])[Xttinds]), 'Split should preserve labels'
    print('Passed!')


def test_softmax(softmax_fun):
    x1d = np.random.randn(5)
    assert np.all(np.isclose(softmax_fun(x1d).sum(axis=-1), 1)), 'Softmax outputs should sum to 1'
    assert np.all(softmax_fun(x1d) >= 0), 'Softmax outputs should be >= 0'
    
    x2d = np.random.randn(10, 5)
    assert softmax_fun(x2d).shape == (10, 5), 'Softmax should return array same shape as input'
    assert np.all(np.isclose(softmax_fun(x2d).sum(axis=-1), 1)), 'Softmax outputs should sum to 1'
    assert np.all(softmax_fun(x2d) >= 0), 'Softmax outputs should be >= 0'
    
    a = np.array([[5, 4, 3], [3, 2, 1], [-5, 4, -3]])
    sma = np.array([[6.65240956e-01, 2.44728471e-01, 9.00305732e-02],
       [6.65240956e-01, 2.44728471e-01, 9.00305732e-02],
       [1.23282171e-04, 9.98965779e-01, 9.10938878e-04]])
    assert np.all(np.isclose(softmax_fun(a), sma)), 'Softmax failed test case'
    print('Passed!')

def test_predict(predict_fun):
    np.random.seed(54)
    w = np.random.randn(3, 50).T
    class model:
        def __init__(self):
            self.weights = w
    
    X = np.random.randn(10, 2)
    y = predict_fun(model(), X)

    assert y.ndim == 1, 'Predictions should be a length N vector'
    assert y.dtype == int, 'Prediction type should be an integer'
    assert np.all(y == np.array([41, 41, 41,  9,  0, 44, 44, 41, 35,  0])), 'Failed test case'
    print('Passed!')

def test_predict_probability(predict_fun):
    np.random.seed(54)
    w = np.random.randn(3, 5).T
    class model:
        def __init__(self):
            self.weights = w
    
    X = np.random.randn(10, 2)
    y = predict_fun(model(), X)

    assert y.shape == (10, 5), 'Predictions should be an N x C matrix'
    assert y.dtype == float, 'Prediction type should be a float'
    assert np.all(np.isclose(y.sum(axis=1), 1)), 'Probabilities should sum to 1 for every observation'
    answer = np.array([[4.26513645e-01, 3.95462714e-01, 6.03729094e-02, 7.75720258e-02,
        4.00787058e-02],
       [2.18701674e-01, 5.65918374e-01, 1.14080109e-01, 4.59756804e-02,
        5.53241621e-02],
       [5.13639999e-04, 6.82355659e-02, 4.49881407e-01, 5.07207028e-04,
        4.80862180e-01],
       [4.77919962e-01, 3.00901298e-01, 6.12563428e-02, 9.66537017e-02,
        6.32686956e-02],
       [2.80859070e-01, 1.05617337e-01, 9.26734944e-02, 1.01709536e-01,
        4.19140563e-01],
       [6.20092374e-01, 2.49211160e-01, 2.36548778e-02, 9.05214541e-02,
        1.65201338e-02],
       [4.65837506e-02, 1.96114486e-01, 2.63632098e-01, 2.16113680e-02,
        4.72058297e-01],
       [7.41180279e-01, 1.73556581e-01, 7.01124530e-03, 7.50289067e-02,
        3.22298809e-03],
       [5.23410993e-01, 3.87011531e-01, 2.09909631e-02, 6.18921267e-02,
        6.69438700e-03],
       [3.37837034e-01, 4.71833500e-01, 7.94856479e-02, 6.47690576e-02,
        4.60747599e-02]])
    assert np.all(np.isclose(y, answer)), 'Failed test case'
    print('Passed!')

def test_nll(nll_fun):
    np.random.seed(54)
    w = np.random.randn(3, 50).T
    class model:
        def __init__(self):
            self.weights = w
    
    X = np.random.randn(10, 2)
    y = np.array([41, 41, 41,  9,  0, 44, 44, 41, 35,  0])
    nll = nll_fun(model(), X, y)
    assert np.isscalar(nll), 'NLL should be a scalar'
    assert np.isclose(nll, 15.519349088554755), 'nll failed test case'
    print('Passed!')


def test_nll_grad(grad_fun):
    np.random.seed(54)
    w = np.random.randn(3, 12).T
    X = np.random.randn(10, 2)
    y = np.random.randint(0, 12, (10,))

    class model:
        def __init__(self):
            self.weights = w
            self.classes = 12
    
    nll_grad = grad_fun(model(), X, y)

    answer = np.array([[-0.76888849, -1.69866702,  0.35616321],
       [ 0.00767945, -0.0183717 ,  0.21642377],
       [ 0.60762504, -1.62256696, -0.40512907],
       [ 0.13154167,  0.06921735,  1.98158209],
       [-0.34329933, -0.32987131, -0.26538862],
       [ 0.0065204 ,  0.19877158, -1.769354  ],
       [-0.04355595, -0.11342692,  0.46434438],
       [-0.4915649 ,  1.4782631 , -0.66433753],
       [-0.52063029, -1.11329253, -0.61249813],
       [ 0.13769193,  0.16466782,  0.40174733],
       [ 0.44391556,  1.77336478, -1.22337152],
       [ 0.83296492,  1.21191181,  1.51981808]])
    
    assert nll_grad.shape == w.shape, 'Gradient shape should match shape of weights'
    assert np.isclose(nll_grad, answer).all(), 'nll_grad failed test case'
    print('Passed!')

