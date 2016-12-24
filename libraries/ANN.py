import numpy as np

class ANN:
    ''' This is an artificial neural network class. It learns using the backpropagation algorithm, and can classify binary as well as multi-class problems. At the moment it can only run in batch learning mode.'''

    def __init__(self, numLayers, Input, target, hiddenNeuronList=[], eta=0.1, mode='batch'):
        ''' Initialize an instance of the machine learning class '''
        self.mode = mode
        self.numLayers = numLayers
        self.numHiddenLayers = numLayers - 2
        self.eta = eta
        self.__Input__ = np.matrix(Input).T

        self.number_of_features = self.__Input__.shape[0]
        self.number_of_training_points = self.__Input__.shape[1]

        self.__Input__ =  np.vstack([self.__Input__,[1]*self.number_of_training_points])
        self.class_labels = set(target)
        self.number_of_classes = len(self.class_labels)
        self.set_target(target)

        if not len(hiddenNeuronList):
            # Should be changed later to something more general
            self.hiddenNeuronList = [self.number_of_features]*self.numHiddenLayers
        else:
            self.hiddenNeuronList = hiddenNeuronList

        self.construct_network()
        print "Network constructed with {} layers, learning rate is {}".format(self.numLayers, self.eta)
        self.connect_layers()
        print "Layers connected"

    def set_target(self, target):
        ''' Setting target to the ANN'''
        try:
            np.shape(self.__Input__)[0] == len(target)

            if self.number_of_classes > 2: # More than binary classification
                self.__target__ = np.zeros((self.number_of_classes, self.number_of_training_points))
                for i, label in enumerate(self.class_labels):
                    for j, t in enumerate(target):
                        if label == t: 
                            self.__target__[i,j] = 1
            else:
                self.__target__ = np.zeros((1, self.number_of_training_points))
                self.__target__[0] = target 

        except:
            return "Lengths of input and target don't match"

    def construct_network(self):
        ''' Construct the different layers and units of the NN '''
        # Input layer Stuff
        self.input_layer = input_layer(self.number_of_features)
        
        # Create Hidden Layers
        self.hidden_layers = [hidden_layer(self.hiddenNeuronList[i], self.number_of_training_points, self.eta ) for i in range(self.numHiddenLayers)]

        # Create output layer
        self.output_layer = output_layer(self.number_of_classes, self.number_of_training_points, self.eta )

        self.layers = [self.input_layer] + self.hidden_layers + [self.output_layer]

    def connect_layers(self):
        '''Connect layers'''
        # Input layer
        self.hidden_layers[0].connect_layer(self.input_layer)
        # Hidden layers
        for n in range(self.numHiddenLayers-1):
            self.hidden_layers[n+1].connect_layer(self.hidden_layers[n])
        # Output layer
        self.output_layer.connect_layer(self.hidden_layers[-1])

    def __error_function__(self, t, o):
        '''This is the error function'''

        return (1./2)*(np.sum(np.square(t-o)))

    def backpropagate(self, target):
        ''' Backpropagation of errors through the NN '''
        self.output_layer.backpropagate(target)
        for layer in self.hidden_layers[::-1]:
            layer.backpropagate()

    def update_weights(self):
        ''' NN weight updates '''
        for layer in self.layers[1:]:
            layer.update()

    def compute_forward(self):
        ''' Forward computation by NN by passing through activation function '''
        self.input_layer.compute_layer(self.__Input__)
        for layer in self.hidden_layers:
            layer.compute_layer()
        self.output_layer.compute_layer()

    def iterate(self, iterations=1):
        ''' This is the main iteration function which forward computes, backpropagates, and updates weights for the NN '''
        error = []
        for i in range(iterations):
            self.compute_forward()
            self.backpropagate(self.__target__)
            self.update_weights()
            error.append(self.__error_function__( self.__target__, self.output_layer.output))
            if i%(iterations/10.) == 0.:
                print "{} iterations, loss = {}".format(i, error[-1])
        if iterations == 1:
            return error[0]
        else:
            return error

class neuron_layer:
    ''' This is a neural network layer class'''

    def __init__(self, N, numDataPoints, eta):
        ''' This initializes a neural network layer '''
        if isinstance(self, hidden_layer):
            self.N = N+1 # Adding bias neurons to the hidden layers
        else:
            if N == 2: #Special provision for binary classification
                self.N = 1
            else:
                self.N = N
        self.neurons = [neuron(self, index) for index in range(self.N)]
        self.eta = eta
        self.output = np.zeros((self.N,numDataPoints))
        self.delta = np.zeros((self.N,numDataPoints))

    def connect_layer(self, prev_layer):
        ''' This connects neural network layers together '''
        self.prev_layer = prev_layer
        self.index = self.prev_layer.index + 1
        prev_layer.set_next_layer(self)
        numEdges = prev_layer.N * self.N
        for n in self.neurons:
            n.initialize_weights(prev_layer.N)

    def compute_layer(self):
        ''' Compute activation for all neurons in layer '''
        for i,n in enumerate(self.neurons):
            self.output[i] = n.compute()
            n.set_w_out()
        return self.output

    def update(self):
        ''' Update weights for all neurons in layer '''
        for i, neuron in enumerate(self.neurons):
            neuron.change_weight(self.eta)

class input_layer(neuron_layer):
    ''' This is the input layer class'''

    def __init__(self, N):
        self.N = N + 1 
        self.index = 0
    
    def compute_layer(self,x):
        self.output = x
        return self.output 
    
    def set_next_layer(self, next_layer):
        self.next_layer = next_layer

class hidden_layer(neuron_layer):
    ''' This is the hidden layer class'''

    def set_next_layer(self, next_layer):
        self.next_layer = next_layer

    def backpropagate(self):
        next_delta = self.next_layer.delta
        # print neuron.w_out, next_delta
        for i, neuron in enumerate(self.neurons):
            self.delta[i] = neuron.set_delta( neuron.output * (1. - neuron.output) * np.dot(neuron.w_out, next_delta))

class output_layer(neuron_layer):
    ''' This is the output layer class'''

    def backpropagate(self, target):
        for i, neuron in enumerate(self.neurons):
            self.delta[i]  = neuron.set_delta( (target[i] - neuron.output) * neuron.output * (1 - neuron.output))

class neuron:
    '''This is a neuron (Units inside a layer) class'''

    def __init__(self, layer, index, activation_method = 'sigmoid', bias_constant=0.99):
        ''' Initialize a neuron instance '''
        self.layer = layer
        self.index = index
        self.activation_method = activation_method
        self.bias_constant = bias_constant

    def set_w_out(self):
        ''' Get all weights going out of the neuron '''
        if isinstance(self.layer, output_layer): 
            self.w_out = None
        elif isinstance(self.layer, hidden_layer):
            w_out = [n.w[self.index] for n in self.layer.next_layer.neurons]
            self.w_out = np.array(w_out)         

    def initialize_weights(self, numInputs):
        ''' Randomly assign initial weights from a uniform distribution '''
        self.w = np.random.uniform(-1, 1, numInputs)
        # self.w = np.zeros(numInputs) # Just for kicks

    def activation(self, input):
        ''' This is our activation function. '''
        if self.activation_method == 'sigmoid':
            return self.sigmoid(input)

    def sigmoid(self, x):
        ''' This is sigmoid activation function. '''
        return 1/(1+np.exp(-x))

    def compute(self):
        if not (isinstance(self.layer, hidden_layer) and self.index == 0):
            input = np.ravel(np.dot( np.transpose(self.w), self.layer.prev_layer.output))
            self.output = self.activation(input)
        else:
            factor = self.bias_constant 
            self.output = np.ones(self.layer.prev_layer.output.shape[1])*factor #Bias units outputing ones all the time.
        return self.output

    def set_delta(self, delta):
        self.delta = delta
        return self.delta

    def change_weight(self, eta):
        ''' Update weights for neuron '''
        self.w += eta * np.ravel(np.dot(self.delta , self.layer.prev_layer.output.T))
