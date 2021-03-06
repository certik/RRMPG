# -*- coding: utf-8 -*-
# This file is part of RRMPG.
#
# RRMPG is free software with the aim to provide a playground for experiments
# with hydrological rainfall-runoff-models while achieving competitive
# performance results.
#
# You should have received a copy of the MIT License along with RRMPG. If not,
# see <https://opensource.org/licenses/MIT>

import unittest
import os

import numpy as np
import pandas as pd

from rrmpg.models import ABCModel, HBVEdu, GR4J
from rrmpg.models.basemodel import BaseModel

class TestBaseModelFunctions(unittest.TestCase):
    """Test all functions implemented in the BaseModel.
    
    These will not be test for all models, but one as an example for one of 
    the models.
    """
    
    def setUp(self):
        self.model = ABCModel()
        self.param_names = ['a', 'b', 'c']
        self.default_bounds =  {'a': (0, 1),
                                'b': (0, 1),
                                'c': (0, 1)}
        self.dtype = np.dtype([('a', np.float64),
                               ('b', np.float64),
                               ('c', np.float64)])
        unittest.TestCase.setUp(self)
        
    def test_get_parameter_names(self):
        self.assertEqual(self.model.get_parameter_names(), self.param_names)
        
    def test_get_params(self):
        params = self.model.get_params()
        for param in self.param_names:
            msg = "Failed, because '{}' not in '{}'".format(param, params.keys)
            self.assertIn(param, params, msg)
            
    def test_get_default_bounds(self):
        bounds = self.model.get_default_bounds()
        self.assertDictEqual(bounds, self.default_bounds)
        
    def test_get_dtype(self):
        self.assertEqual(self.dtype, self.model.get_dtype())
        
    def test_random_params_in_default_bounds(self):
        params = self.model.get_random_params()
        bnds = self.default_bounds
        
        for p, val in params.items():
            msg = ["Failed for param: '{}', which has a ".format(p),
                   "a value of {}, but lower bounds ".format(val),
                   "is {} and upper bound {}.".format(bnds[p][0], bnds[p][1])]
            self.assertTrue(bnds[p][0] <= val <= bnds[p][1], "".join(msg))
            
    def test_set_params(self):
        rand_params = self.model.get_random_params()
        self.model.set_params(rand_params)
        self.assertDictEqual(rand_params, self.model.get_params()) 
        
        
class TestABCModel(unittest.TestCase):
    """Test ABC-Model specific functions."""
    
    def setUp(self):
        self.model = ABCModel()
        unittest.TestCase.setUp(self)
        
    def test_model_subclass_of_basemodel(self):
        self.assertTrue(issubclass(self.model.__class__, BaseModel))
        
    def test_simulate_zero_rain(self):
        qsim = self.model.simulate(np.zeros(100))
        self.assertEqual(np.sum(qsim), 0)
        
    def test_simulate_negative_rain(self):
        with self.assertRaises(ValueError) as context:
            self.model.simulate([-1,1,1])
        expr = ("In the precipitation array are negative values." in
                str(context.exception)) 
        self.assertTrue(expr)


class TestHBVEdu(unittest.TestCase):
    """Test HBVEdu specific functions."""
    
    def setUp(self):
        self.model = HBVEdu(area=100)
        
    def test_model_subclass_of_basemodel(self):
        self.assertTrue(issubclass(self.model.__class__, BaseModel))    
        
    def test_simulate_zero_rain(self):
        qsim = self.model.simulate(temp=np.random.uniform(-15,25,100),
                                   prec=np.zeros(100),
                                   month=np.random.randint(1,12,100),
                                   PE_m=np.random.uniform(0,4,12),
                                   T_m=np.random.uniform(-5,15,12))
        self.assertEqual(np.sum(qsim), 0)
        
    def test_simulate_negative_rain(self):
        with self.assertRaises(ValueError) as context:
            self.model.simulate(temp=np.random.uniform(-15,25,100),
                                prec=np.arange(-1,99),
                                month=np.random.randint(1,12,100),
                                PE_m=np.random.uniform(0,4,12),
                                T_m=np.random.uniform(-5,15,12))
        expr = ("In the precipitation array are negative values." in
                str(context.exception)) 
        self.assertTrue(expr)
    
class TestGR4J(unittest.TestCase):
    """Test the GR4J Model.
    
    This model is validated against the Excel implementation provided by the 
    model authors.
    """
    
    def setUp(self):
        # parameters are taken from the excel sheet
        params = {'x1': np.exp(5.76865628090826), 
                  'x2': np.sinh(1.61742503661094), 
                  'x3': np.exp(4.24316129943456), 
                  'x4': np.exp(-0.117506799276908)+0.5}
        self.model = GR4J(params=params)
        
    def test_model_subclass_of_basemodel(self):
        self.assertTrue(issubclass(self.model.__class__, BaseModel))  
        
    def test_simulate_zero_rain(self):
        qsim = self.model.simulate(prec=np.zeros(100),
                                   etp=np.random.uniform(0,3,100),
                                   s_init=0, r_init=0)
        self.assertEqual(np.sum(qsim), 0)
        
    def test_simulate_compare_against_excel(self):
        # intial states are taken from excel
        s_init = 0.6
        r_init = 0.7
        test_dir = os.path.dirname(__file__)
        data_file = os.path.join(test_dir, 'data', 'gr4j_example_data.csv')
        data = pd.read_csv(data_file, sep=',')
        qsim = self.model.simulate(data.prec, data.etp, s_init=s_init, 
                                   r_init=r_init, return_storage=False)
        self.assertTrue(np.allclose(qsim, data.qsim_excel))
        