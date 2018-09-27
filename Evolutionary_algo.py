import keras  
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.callbacks import TensorBoard
import numpy as np
import os
import random


#Basic keras model for doing deep learning
model = Sequential()

model.add(Conv2D(32, (3, 3), padding='same',
                 input_shape=(176, 200, 3),
                 activation='relu'))
model.add(Conv2D(32, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.4))

model.add(Conv2D(64, (3, 3), padding='same',
                 activation='relu'))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.4))

model.add(Conv2D(128, (3, 3), padding='same',
                 activation='relu'))
model.add(Conv2D(128, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.4))

model.add(Flatten())
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.5))

model.add(Dense(4, activation='softmax'))

learning_rate = 0.0001
opt = keras.optimizers.adam(lr=learning_rate, decay=1e-6)

model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])

tensorboard = TensorBoard(log_dir="logs/Version_1.0.0")

directory = "train_data"

#iterates over all of the decision lists and return their lengths
def return_data_length():
    choices = {"no_attacks": no_attacks,
               "attack_closest_to_nexus": attack_closest_to_nexus,
               "attack_enemy_structures": attack_enemy_structures,
               "attack_enemy_start": attack_enemy_start}

    total_data = 0

    lengths = []
    for choice in choices:
        total_data += len(choices[choice])
        lengths.append(len(choices[choice]))

    return lengths

epochs = 10

for i in range(epochs):
    current = 0
    incrementSize = 200
    not_max = True
    files = os.listdir(dir)
    maximum = len(all_files)
    #We wanna shuffle files, so our batches are random
    random.shuffle(files)
    while not maximum:
        #each array represents the target of an attack
        idle = []
        units = []
        structures = []
        nexus = []

        for file in files[current:current + increment]:
            path = os.path.join(train_data,file)
            data_set = np.load(path)
            data_set = list(data_set)
            for data in data_set:
                decision = np.argmax(data[0])
                if decision == 0:
                    idle.append(data)
                elif decision == 1:
                    units.append(data)
                elif decision == 2:
                    structures.append(data)
                elif decision == 3:
                    nexus.append(data)

        lengths = return_data_length()
        min_length = min(lengths)
        # slice all the data to be the same size
        random.shuffle(idle)
        random.shuffle(units)
        random.shuffle(structures)
        random.shuffle(nexus)

        idle = idle[:min_length]
        units = units[:min_length]
        structures = structures[:min_length]
        nexus = nexus[:min_length]


        train_data = no_attacks + attack_closest_to_nexus + attack_enemy_structures + attack_enemy_start

        random.shuffle(train_data)

        test_size = 100
        batch_size = 128

        #Setup our train data and test data, then pass it into our model
        x_train = np.array([i[1] for i in train_data[:-test_size]]).reshape(-1, 176, 200, 3)
        y_train = np.array([i[0] for i in train_data[:-test_size]])

        x_test = np.array([i[1] for i in train_data[-test_size:]]).reshape(-1, 176, 200, 3)
        y_test = np.array([i[0] for i in train_data[-test_size:]])

        model.fit(x_train, y_train,
                  batch_size=batch_size,
                  validation_data=(x_test, y_test),
                  shuffle=True,
                  verbose=1, callbacks=[tensorboard])
        #save the model
        model.save("BasicCNN-{}-epochs-{}-LR-STAGE1".format(hm_epochs, learning_rate))
        current += increment
        if current > maximum:
            not_maximum = False