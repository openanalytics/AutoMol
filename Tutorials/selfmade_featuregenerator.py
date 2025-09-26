"""
Example of external feature generator for AutoMol

These classes inherit from the parent class FeatureGenerator. 
class FeatureGenerator():
    def __init__(self):
        self.nb_features=-1
        self.names=[]
        self.generator_name=''
    
    def get_nb_features(self):
        assert self.nb_features>0, 'method not correctly created, negative number of features'
        return self.nb_features
    
    def check_consistency(self):
        assert len(self.names)==self.nb_features, 'Provided number of names is not equal to provided number of features'
        assert self.nb_features>0, 'negative number of features'
    
    def generate(self,smiles):
        pass
    
    def get_names(self):
        return self.names
    
    def get_generator_name(self):
        return self.generator_name
        
Important is to set the attributes: 
    names
    nb_features

and to implement the function:
    generate(self,smiles)
        with smiles a list of smiles 
    that returns a numpy 2d array with the features (rows= samples, columns=features)

"""
from automol.feature_generators import FeatureGenerator

import requests
import json
import torch
from torch import nn
import os
import numpy as np

class DeployedModel(FeatureGenerator):
    def __init__(self,feature_properties=None,link="https://hypotheticallink.com/model/v/02/"):
        super(DeployedModel, self).__init__()
        self.link=link
        response = requests.post(self.link, 
                json={
                        'molecule': {'SMILES': ['Oc1ccc(cc1OC)C=O'], 'sdf': None}, 'user': 'autoML-user'
                    } #{"SMILES": ["COC","CCC"]}
            ) 
        out=response.json()
        if feature_properties is None:
            self.feature_properties=[key for key in out.keys() if key != '']
        else:
            for p in feature_properties:
                assert f'{p}'in out.keys(), f'Property {p} not in output provided model'
            self.feature_properties=feature_properties
        #self.nb_features and self.names Required for FeatureGenerator!
        self.nb_features=len(self.feature_properties)
        self.names=[f'DeployedModel_{p}' for p in self.feature_properties]
    
    def generate(self,smiles):
        self.check_consistency()
        #smiles per smiles
        response_dicts=[requests.post(self.link, 
                json={
                        'molecule': {'SMILES': smi, 'sdf': None}, 'user': 'autoML-user'
                    } #{"SMILES": ["COC","CCC"]}
            ).json() for smi in smiles]
        return np.stack([ np.stack([out[f'{p}'] for out in response_dicts],axis=0) for p in self.feature_properties], axis=-1)
    