# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 09:31:23 2017

@author: junfeng
"""

import json
import random
import sys
import numpy as np

class QuadraticCost(object):
    @staticmethod
    def fn(a,y):
        """
        return the cost associated with an output "a" and desired output "y"
        """
        return 0.5*np.linalg.norm(a-y)**2
    @staticmethod
    def delta(z,a,y):
        """
        return the error delta from the output layer.
        """
        return (a-y)* sigmoid_prime(z)
    
    
class CrossEntropyCost(object):
    @staticmethod
    def fn(a,y):
        """
        return the cost associated with an output "a" and desired output "y".Note 
        that np.nan_to_num is used to ensure numerical stability. in particular,
        if both "a" and "y" have a 1.0 in the same slot, then the expression
        (1-y)*np.log(1-a) return nan. The np.nan_to_num ensures that that is 
        converted to the correct value (0.0)
        """
        return np.sum(np.nan_to_num(-y*np.log(a) - (1-y)*np.log(1-a)))
    
    @staticmethod
    def delta(z,a,y):
        """
        return the error delta from the output layer. Note that the parameter
        "z" is not used by the method. It is included in the method's parameter
        in order to make the interface consistent with the delta method for other 
        cost classes.
        """
        return (a-y)
class Network(object):
    def __init__(self, sizes, cost = CrossEntropyCost):
        """
        The list "sizes" contains the number of neurons in the respective layers 
        of the network
        """
        self.num_layers = len(sizes)
        self.sizes = sizes
        self.default_weight_initializer()
        self.cost = cost
    
    def default_weight_initializer(self):
        """
        Initiaize each weight using a Gaussian distribution with mean o and 
        standard deviation 1 over the square root of the number of weights connecting 
        to the same neuron.
        """
        self.biases = [np.random.randn(y, 1) for y in self.sizes[1:]]
        self.weights = [np.random.randn(y, x)/np.sqrt(x)
                        for x, y in zip(self.sizes[:-1], self.sizes[1:])]
        
    def large_weight_initializer(self):
        """
        Initialize the weights using a Gaussian distribution with mean 0 and 
        standard deviation 1.
        """
        self.biases = [np.random.randn(y, 1) for y in self.sizes[1:]]
        self.weights = [np.random.randn(x, y)
                        for x, y in zip(self.sizes[1:], self.sizes[:-1])]
        
    def feedforward(self, a):
        """
        return the output of network if "a" is output
        """
        for b,w in zip(self.biases, self.weights):
            a = sigmoid(np.dot(w, a)+b)
        return a
    
    def SGD(self, training_data, epochs, mini_batch_size, eta, 
           lmbda = 0.0,
           evaluation_data = None,
           monitor_evaluation_cost = False,
           monitor_evaluation_accuracy = False,
           monitor_training_cost = False,
           monitor_training_accuracy = False,
           early_stopping_n = 0):
        """
        training the neural network using mini_batch stochastic gradient descent
        . the "training_data" is a list of tuples"(x,y)", the other non-optional 
        parameters are self-explantory, as is the regularization parameter "lambda"
        the method also accepts "evaluation_data", usually either the validation 
        or test data. We can monitor the cost and accuracy on either the evaluation
        or training_data, by setting the appropriate flags.
        the method returns a tuple containing four lists: the (per-epoch) costs 
        on the evaluation data, the accuracies on the evaluation data, the cost
        and the accuracies in the training data
        note that the lists are empty if the corresponding flag is not set
        """
        
        # early stopping functionality
        best_accuracy=1
        
        training_data = list(training_data)
        n = len(training_data)
        
        if evaluation_data:
            evaluation_data = list(evaluation_data)
            n_data = len(evaluation_data)
            
        # early stopping functionality
        best_accuracy = 0
        no_accuracy_change = 0
        
        
        evaluation_cost, evaluation_accuracy = [], []
        training_cost, training_accuracy = [], []
        for j in range(epochs):
            random.shuffle(training_data)
            mini_batches = [training_data[k:k+mini_batch_size] 
                           for k in range(0,n, mini_batch_size)]
            for mini_batch in mini_batches:
                self.update_mini_batch(
                mini_batch, eta,lmbda,len(training_data))
            print("Epoch {} training complete".format(j))
            
            if monitor_training_cost:
                cost = self.total_cost(training_data, lmbda)
                training_cost.append(cost)
                print ("cost on training_data:{}".format(cost))
            
            if monitor_training_accuracy:
                accuracy = self.accuracy(training_data, convert = True)
                training_accuracy.append(accuracy)
                print("accuracy on training data: {} / {}".format(accuracy,n))
                
            if monitor_evaluation_cost:
                cost = self.total_cost(evaluation_data, lmbda, convert = True)
                evaluation_cost.append(cost)
                print('cost on evaluation data:{}'.format(cost))
                
            if monitor_evaluation_accuracy:
                accuracy = self.accuracy(evaluation_data)
                evaluation_accuracy.append(accuracy)
                print("accuracy on evaluation data:{} / {}".format(self.accuracy(evaluation_data), n_data))
                
            # early stopping 
            if early_stopping_n > 0:
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    no_accuracy_change = 0
                else:
                    no_accuracy_change +=1
                    
                if (no_accuracy_change == early_stopping_n):
                     return evaluation_cost, evaluation_accuracy, training_cost, training_accuracy
                
        return evaluation_cost, evaluation_accuracy, training_cost, training_accuracy
    
    def update_mini_batch(self, mini_batch, eta, lmbda,n):
        """
        updata the network's weights and biases by applying gradient descent 
        using backpropagation to a single mini batch.
        """
        
        nabla_b = [np.zeros(b.shape) for b in self.biases]
        nabla_w = [np.zeros(w.shape) for w in self.weights]
        for x, y in mini_batch:
            delta_nabla_b, delta_nabla_w = self.backprop(x,y)
            nabla_b = [nb+dnb for nb, dnb in zip(nabla_b, delta_nabla_b)]
            nabla_w = [nw+dnw for nw, dnw in zip(nabla_w, delta_nabla_w)]
        self.weights = [(1-eta*(lmbda/n))*w-(eta/len(mini_batch))*nw
                       for w, nw in zip(self.weights, nabla_w)]
        self.biases = [b-(eta/len(mini_batch))*nb
                      for b,nb in zip(self.biases, nabla_b)]
        
    def backprop(self, x, y):
        """
        Return a tuple ``(nabla_b, nabla_w)`` representing the																		  
        gradient for the cost function C_x.  ``nabla_b`` and
        ``nabla_w`` are layer-by-layer lists of numpy arrays, similar
        to ``self.biases`` and ``self.weights``.
        """
        nabla_b = [np.zeros(b.shape) for b in self.biases]
        nabla_w = [np.zeros(w.shape) for w in self.weights]
        # feedforward
        activation = x
        activations = [x]
        zs = []
        for b, w in zip(self.biases, self.weights):
            z = np.dot(w,activation) +b
            zs.append(z)
            activation = sigmoid(z)
            activations.append(activation)
            # backward pass
        delta = (self.cost).delta(zs[-1], activations[-1], y)
        nabla_b[-1] = delta
        nabla_w[-1] = np.dot(delta, activations[-2].transpose())
            
        for l in range(2, self.num_layers):
            z = zs[-l]
            sp = sigmoid_prime(z)
            delta = np.dot(self.weights[-l+1].transpose(), delta) *sp
            nabla_b[-l] = delta
            nabla_w[-l] = np.dot(delta, activations[-l-1].transpose())
        return (nabla_b, nabla_w)
    
    def accuracy(self, data, convert = False):
        """
        return the number of inputs in "data" for which the neural network 
        output is assumed to be the index of whichever neuron in the final 
        layer has the highest activation
        """
        if convert:
            results = [(np.argmax(self.feedforward(x)), np.argmax(y))
                      for (x,y) in data]
        else:
            results =  [(np.argmax(self.feedforward(x)),y) 
                       for (x,y) in data]
        result_accuracy = sum(int(x==y) for (x,y) in results)
        return result_accuracy
    
    def total_cost(self, data, lmbda, convert = False):
        """
        return the total cost for the data set "data". the flag "convert"
        should be set to FALSE if the data set is the training data
        """
        cost = 0.0
        for x,y in data:
            a = self.feedforward(x)
            if convert:
                y = vectorized_result(y)
            cost += self.cost.fn(a,y)/len(data)
            cost += 0.5* (lmbda/len(data))*sum(np.linalg.norm(w)**2 for w in self.weights)
        return cost
    def save(self, filename):
        """
        save the neural network to the file "filename"
        """
        data = {"sizes": self.sizes,
               "weights": [w.tolist() for w in self.weights],
               "biases": [b.tolist() for b in self.biases],
               "cost": str(self.cost.__name__)}
        f = open(filename,"w")
        json.dump(data, f)
        f.close()
        
        
def load(filename):
    """
    load a neural network from the file "filename", return an instance of Networl

    """
    f = open(filename,'r')
    data = json.load(f)
    f.close()
    cost = getattr(sys.modules[__name__], data["cost"])
    net = Network(data["sizes"], cost = cost)
    net.weights = [np.array(w) for w in data["weights"]]
    net.biases = [np.array(b) for b in data['biases']]
    return net
#### Miscellaneous function
def vectorized_result(j):
    """
    return a 10-dimensional unit vector with a 1.0 in the j th position and 
    zeros eleswise. This is used to convert a digital into a corresponding 
    desired output from the neural network.
    """
    e = np.zeros((10,1))
    e[j] = 1.0
    return e

def sigmoid(z):
    return 1.0/(1.0+np.exp(-z))

def sigmoid_prime(z):
    return sigmoid(z)*(1 - sigmoid(z))
            
        
    
        