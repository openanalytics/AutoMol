"""implementation of the different feature generators and their base class.

Authors: Joris Tavernier and Marvin Steijaert

Contact: joris.tavernier@openanalytics.eu, Marvin.Steijaert@openanalytics.eu

All rights reserved, Open Analytics NV, 2021-2025.
"""

# from .model import *  # Removed: model.py no longer exists (PyTorch dependency removed)

import pandas as pd

import numpy as np
from pathlib import Path
from rdkit import __version__ as rdkit_version
from rdkit import Chem
from rdkit.Chem import Descriptors, MolFromSmiles, AllChem
from rdkit.ML.Descriptors import MoleculeDescriptors


from importlib_resources import files


def retrieve_default_offline_generators(model='CHEMBL', radius=2, nbits=2048):
    """
    Function that returns a dictionary of default internal feature generators.
    
    Args:
        model: string that to define which kind of Deeplearning generated features. Reflects the smiles used for training the encoder.
        radius: radius of ecfp generation
        nbits: size of the ecfp features
    """

    return {'Bottleneck':OnnxBottleneckTransformer(),
            'rdkit':RDKITGenerator(),
            f'fps_{nbits}_{radius}':ECFPGenerator(radius=radius, nBits =nbits)
           }

###############################
class FeatureGenerator():
    def __init__(self):
        """
        Initialization of the base class
        """
        ## number of features
        self.nb_features=-1
        ## list of the names of the features
        self.names=[]
        ## the name of the generator
        self.generator_name=''
    
    def get_nb_features(self):
        """
        getter for the number of features.
        
        includes an assert that number of features is positive.
        
        Returns
            nb_features (int): number of features
        """
        assert self.nb_features>0, 'method not correctly created, negative number of features'
        return self.nb_features
    
    def check_consistency(self):
        """
        checks if the number of features is positive and the length of the feature names equal the number of features
        """
        assert len(self.names)==self.nb_features, 'Provided number of names is not equal to provided number of features'
        assert self.nb_features>0, 'negative number of features'
    
    def generate(self,smiles):
        """
        generate the feature matrix from a given list of smiles
        
        Args:
            smiles: list of smiles (list of strings)
        
        Returns:
            X: feature matrix as numpy array 
        """
        pass
    
    def generate_w_pairs(self,smiles,original_indices,new_indices):
        """
        generate the feature matrix from a given list of smiles
        
        Args:
            smiles: list of smiles (list of strings)
            original_indices: indices for pairs of ligands without reindexing after datasplitting
            new_indices: list indices for pairs of ligands with reindexing after datasplitting
        Returns:
            X: feature matrix as numpy array 
        """
        X=self.generate(smiles)
        X_p=np.zeros((len(new_indices),2*X.shape[1]))           
        for idx,(i,j) in enumerate(new_indices):
            X_p[idx,:]=np.hstack((X[i,:],X[j,:]))
        return X_p
    
    def get_names(self):
        """
        getter for the names of the features
        
        Returns:
            names (List[str]): list of names
        """
        return self.names
    
    def get_generator_name(self):
        """
        getter for the generator name
        
        Returns:
            generator_name (str): the name of the generator
        """
        return self.generator_name

###############################    
class RDKITGenerator(FeatureGenerator):
    """
    feature generator returning the rdkit descriptors
    """

    def __init__(self):
        """
        Initialization 
        """
        ## list of rdkit names from rdkit.Chem.Descriptors.descList
        self.rdkitnames=[ n for n,f in Descriptors.descList]
        ## descriptor calculator MoleculeDescriptors.MolecularDescriptorCalculator(self.rdkitnames)
        self.calculator = MoleculeDescriptors.MolecularDescriptorCalculator(self.rdkitnames)
        ## list of names of the features
        self.names= self.calculator.GetDescriptorNames()
        ## number of features
        self.nb_features=len(self.rdkitnames)
        ## generator name
        self.generator_name=f'automol_rdkit_{rdkit_version}'
        
    def get_descriptor(self,s):
        """
        retrieve rdkit descriptors for given smiles s
        
        return tuple of nans if the rdkit fails to calculate descriptors
        
        Args:
            s (str): smiles string
        
        Returns:
            rdkit descriptors or nans
        """
        if s=="" or s is None:
            return self.nb_features*(np.nan,)
        try:
            m=MolFromSmiles(s)
            if m :
                return self.calculator.CalcDescriptors(m)
            else:
                return  self.nb_features*(np.nan,)
        except:
            return self.nb_features*(np.nan,)
        
    def generate(self,smiles):
        """
        Generate all given descriptors for given list of smiles and return as numpy array
        
        Args:
            smiles: list of smiles (list of strings)
        
        Returns:
            des: feature matrix as numpy array 
        """
        des = np.array([self.get_descriptor(x) for x in smiles])
        #test nan 
        #des[-1]=np.array(self.nb_features*(np.nan,))
        return des
    
###############################
class ECFPGenerator(FeatureGenerator):
    """
    The chemical fingerprints generator using rdkit
    """

    def __init__(self,radius=2, nBits =2048,useChirality= False,useFeatures= False):
        """
        Initialization of the ecfp generator
        
        see rdkit.AllChem.GetMorganFingerprintAsBitVect for details on the morgan fingerprint generation
        
        Args:
            radius: radius for morgan fingerprints [=2]
            nBits: number of bits used [=2048]
            useChirality: boolean to set to use chirality when computing fps[=False]
            useFeatures: boolean to set [=False]
        """
        ## radius
        self.radius=int(radius)
        ## nbits
        self.nBits=int(nBits)
        ## boolean to indicated use of chirality when computing fps
        self.useChirality=useChirality
        ## boolean to indicated use of features when computing fps
        self.useFeatures=useFeatures
        ## number of features
        self.nb_features=int(nBits)
        ## list of feature names
        self.names=[f'fps_{i}_of_{nBits}_radius_{radius}' for i in range(int(nBits))]
        ## generator name
        self.generator_name=f'automol_ecfp_{nBits}_radius_{radius}_rdkit_{rdkit_version}'
    
    def generate(self,smiles):
        """
        Generate ecfp for given list of smiles and return as numpy array
        
        Args:
            smiles: list of smiles (list of strings)
        
        Returns:
            X: feature matrix as numpy array
        """
        #mols =[Chem.MolFromSmiles(s) for s in smiles]
        
        return np.array([np.array(fps) for fps in self.generate_BitVect(smiles)],dtype=float)
        #test nan 
        #outputs=np.array([np.array(fps) for fps in self.generate_BitVect(smiles)],dtype=float)
        #outputs[-1]=np.array(self.nb_features*(0,))
        #return outputs
    
    def generate_BitVect(self,smiles):
        """generate the features as BitVects 
        
        Args:
            smiles (list[str]): list of smiles (list of strings)
        
        Returns:
            The list of bitVect belonging to the given smiles
        """
        def getFP(s):
            try:
                return AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(s), radius=self.radius,
                                                     nBits=self.nBits,
                                                     useChirality=self.useChirality,useFeatures=self.useFeatures)
            except:
                return self.nBits*[np.nan]
        return [getFP(s) for s in smiles]
                    
class MolfeatGenerator(FeatureGenerator):
    def __init__(self):
        super().__init__()
    
    def generate(self, smiles):
        self.check_consistency()
        st=0
        end=0
        X_list=[]
        while end < (len(smiles)):
            end= min(st+self.batch_size, len(smiles))
            smiles_l=smiles[st:end]
            features = np.full([len(smiles_l), self.nb_features], np.nan)
            indices = []
            structures = []
            for i, s in enumerate(smiles_l):
                if s is None or s=='':
                    continue
                try:
                    m=Chem.MolFromSmiles(s)
                except Exception:
                    continue
                if m is not None:
                    indices.append(i)
                    structures.append(Chem.MolToSmiles(m))

            if structures:
                features[indices] = np.stack(self.model(structures))
            
            st+=self.batch_size
            X_list.append(features)
        return np.concatenate(X_list, axis=0)

class MolfeatPretrainedHFTransformer(MolfeatGenerator):
    def __init__(self, kind='MolT5', notation='smiles', dtype=float,max_length=220,batch_size=250):
        from molfeat.trans.pretrained.hf_transformers import PretrainedHFTransformer
        
        super().__init__()
        self.model = PretrainedHFTransformer(kind=kind, notation=notation, dtype=dtype,max_length=max_length)
        
        X_try=np.stack(self.model(['Oc1ccc(cc1OC)C=O']))
        self.nb_features=X_try.shape[1]
        self.generator_name = f'automol_PretrainedHFTransformer_{kind}'
        self.names.extend(f'feature_{x}' for x in range(self.nb_features))
        self.batch_size=batch_size


class MolfeatFPVecTransformer(MolfeatGenerator):
    def __init__(self, kind='desc2D', dtype=float,batch_size=250):
        from molfeat.trans.fp import FPVecTransformer
        
        super().__init__()
        self.model = FPVecTransformer(kind=kind, dtype=dtype)
        
        X_try=np.stack(self.model(['Oc1ccc(cc1OC)C=O']))
        self.nb_features=X_try.shape[1]
        self.generator_name = f'automol_FPVecTransformer_{kind}'
        self.names.extend(f'feature_{x}' for x in range(self.nb_features))
        self.batch_size=batch_size
        
class Molfeat3DFPVecTransformer(MolfeatGenerator):
    def __init__(self, kind='desc2D', dtype=float,batch_size=250,seed=42):
        from molfeat.trans.fp import FPVecTransformer
        
        super().__init__()
        self.model = FPVecTransformer(kind=kind, dtype=dtype)
        self._seed=seed
        
        m = Chem.MolFromSmiles('Oc1ccc(cc1OC)C=O')
        m = Chem.AddHs(m)
        AllChem.EmbedMolecule(m, randomSeed=self._seed)
        X_try=np.stack(self.model([m]))
        self.nb_features=X_try.shape[1]
        self.generator_name = f'automol_FPVecTransformer_{kind}'
        self.names.extend(f'feature_{x}' for x in range(self.nb_features))
        self.batch_size=batch_size
        
    def generate(self, smiles):
        self.check_consistency()
        st=0
        end=0
        X_list=[]
        while end < (len(smiles)):
            end= min(st+self.batch_size, len(smiles))
            smiles_l=smiles[st:end]
            features = np.full([len(smiles_l), self.nb_features], np.nan)
            indices = []
            structures = []
            for i, s in enumerate(smiles_l):
                if s is None or s=='':
                    continue
                try:
                    m = Chem.MolFromSmiles(s)  # talidomide
                    m = Chem.AddHs(m)
                    AllChem.EmbedMolecule(m, randomSeed=self._seed)
                except Exception:
                    continue
                if m is not None:
                    indices.append(i)
                    structures.append(m)

            if structures:
                features[indices] = np.stack(self.model(structures))

            st+=self.batch_size
            X_list.append(features)
        return np.concatenate(X_list, axis=0)


class MolfeatMoleculeTransformer(MolfeatGenerator):
    def __init__(self, featurizer='mordred', dtype=float,batch_size=250):
        from molfeat.trans import MoleculeTransformer
        
        super().__init__()
        self.model = MoleculeTransformer(featurizer=featurizer, dtype=dtype)
        
        X_try=np.stack(self.model(['Oc1ccc(cc1OC)C=O']))
        self.nb_features=X_try.shape[1]
        if isinstance(featurizer,str):
            self.generator_name = f'automol_MoleculeTransformer_{featurizer}'
        else:
            self.generator_name = f'automol_MoleculeTransformer'
        self.names.extend(f'feature_{x}' for x in range(self.nb_features))
        self.batch_size=batch_size
        
class Molfeat3DMoleculeTransformer(MolfeatGenerator):
    def __init__(self, featurizer='mordred', dtype=float,batch_size=250,seed=42):
        from molfeat.trans import MoleculeTransformer
        
        super().__init__()
        self._seed=seed
        self.model = MoleculeTransformer(featurizer=featurizer, dtype=dtype)
        
        m = Chem.MolFromSmiles('Oc1ccc(cc1OC)C=O')
        m = Chem.AddHs(m)
        AllChem.EmbedMolecule(m, randomSeed=self._seed)
        X_try=np.stack(self.model([m]))
        self.nb_features=X_try.shape[1]
        if isinstance(featurizer,str):
            self.generator_name = f'automol_3dMoleculeTransformer_{featurizer}'
        else:
            self.generator_name = f'automol_3dMoleculeTransformer'
        self.names.extend(f'feature_{x}' for x in range(self.nb_features))
        self.batch_size=batch_size        
        
    def generate(self, smiles):
        self.check_consistency()
        st=0
        end=0
        X_list=[]
        while end < (len(smiles)):
            end= min(st+self.batch_size, len(smiles))
            smiles_l=smiles[st:end]
            features = np.full([len(smiles_l), self.nb_features], np.nan)
            indices = []
            structures = []
            for i, s in enumerate(smiles_l):
                if s is None or s=='':
                    continue
                try:
                    m = Chem.MolFromSmiles(s)  # talidomide
                    m = Chem.AddHs(m)
                    AllChem.EmbedMolecule(m, randomSeed=self._seed)
                except Exception:
                    continue
                if m is not None:
                    indices.append(i)
                    structures.append(m)

            if structures:
                features[indices] = np.stack(self.model(structures))
            
            st+=self.batch_size
            X_list.append(features)
        return np.concatenate(X_list, axis=0)
    
        

class MolfeatPretrainedDGLTransformer(MolfeatGenerator):
    def __init__(self, kind='gin_supervised_edgepred', dtype=float,batch_size=250):
        from molfeat.trans.pretrained import PretrainedDGLTransformer
        
        super().__init__()
        self.model =  PretrainedDGLTransformer(kind=kind, dtype=dtype)
        
        X_try=np.stack(self.model(['Oc1ccc(cc1OC)C=O']))
        self.nb_features=X_try.shape[1]
        self.generator_name = f'automol_MPretrainedDGLTransformer_{kind}'
        self.names.extend(f'feature_{x}' for x in range(self.nb_features))
        self.batch_size=batch_size

    
class MolfeatGraphormerTransformer(MolfeatGenerator):
    def __init__(self, kind='pcqm4mv2_graphormer_base', dtype=float,batch_size=250):
        from molfeat.trans.pretrained import GraphormerTransformer
        
        super().__init__()
        self.model =  GraphormerTransformer(kind=kind, dtype=dtype)
        
        X_try=np.stack(self.model(['Oc1ccc(cc1OC)C=O']))
        self.nb_features=X_try.shape[1]
        self.generator_name = f'automol_GraphormerTransformer_{kind}'
        self.names.extend(f'feature_{x}' for x in range(self.nb_features))
        self.batch_size=batch_size



from pathlib import Path
import os
from typing import List, Optional, Union

import numpy as np

from .tokenization import Vocabulary, SmilesTokenizer


class OnnxBottleneckTransformer(FeatureGenerator):
    """
    ONNX Runtime version of BottleneckTransformer.

    Generates 250-dimensional features from SMILES strings using a
    pre-trained transformer encoder exported to ONNX format.

    No PyTorch required for inference.

    Attributes:
        n_features: Number of features (250)
        names: Feature names
        session: ONNX Runtime inference session
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        vocab_path: Optional[str] = None,
        providers: Optional[List[str]] = None,
        batch_size: int = 100,
        seq_len: int = 220,
    ):
        """
        Initialize the ONNX-based bottleneck transformer.

        Args:
            model_path: Path to ONNX model file. If None, uses default.
            vocab_path: Path to vocabulary JSON file. If None, uses default.
            providers: ONNX Runtime execution providers. Default: ['CPUExecutionProvider']
            batch_size: Batch size for processing (for memory efficiency)
            seq_len: Maximum sequence length for SMILES
        """
        super().__init__()

        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError(
                "ONNX Runtime is required for inference. "
                "Install with: pip install onnxruntime"
            )

        # Default paths
        base_dir = os.path.dirname(os.path.realpath(__file__))

        if model_path is None:
            model_path = base_dir + '/bottleneck_encoder.onnx'
        if vocab_path is None:
            vocab_path = base_dir + '/vocab.json'

        self.model_path = model_path
        self.vocab_path = vocab_path
        self.batch_size = batch_size
        self.seq_len = seq_len

        # Initialize tokenizer with vocabulary
        self.tokenizer = SmilesTokenizer(
            vocab_path=vocab_path,
            max_seq_len=seq_len,
            add_sos=True,
            add_eos=True,
        )

        # Create ONNX Runtime session
        providers = providers or ['CPUExecutionProvider']

        # Check if model file exists
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"ONNX model not found at {model_path}. "
                "Run the conversion script first: "
                "python -m automol_onnx.conversion.export_bottleneck"
            )

        self.session = ort.InferenceSession(model_path, providers=providers)

        # Get input/output names from model
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        # Feature configuration
        self.nb_features = 250
        self.names = [f'Bottleneck_{i}_of_{self.nb_features}_model_CHEMBL' for i in range(self.nb_features)]
        self.generator_name = f'automol_onnx_bn_{Path(model_path).stem}'

    def _run_inference(self, input_ids: np.ndarray) -> np.ndarray:
        """
        Run ONNX inference on tokenized input.

        Args:
            input_ids: Token array of shape [seq_len, batch_size]

        Returns:
            Feature array of shape [batch_size, 250]
        """
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: input_ids}
        )
        return outputs[0]

    def generate(self, smiles: Union[List[str], str]) -> np.ndarray:
        """
        Generate features for SMILES strings.

        Args:
            smiles: Single SMILES string or list of SMILES

        Returns:
            numpy array of shape (n_samples, 250)
        """
        # Handle single SMILES
        if isinstance(smiles, str):
            smiles = [smiles]

        # Handle pandas Series/DataFrame
        if hasattr(smiles, 'tolist'):
            smiles = smiles.tolist()

        # Process in batches for memory efficiency
        all_features = []

        for start_idx in range(0, len(smiles), self.batch_size):
            end_idx = min(start_idx + self.batch_size, len(smiles))
            batch = smiles[start_idx:end_idx]

            # Tokenize batch: [seq_len, batch_size]
            input_ids = self.tokenizer.tokenize_batch(batch)

            # Run inference: [batch_size, 250]
            features = self._run_inference(input_ids)

            all_features.append(features)

        # Concatenate all batches
        return np.vstack(all_features)

    def __call__(
        self,
        smiles: Union[List[str], str],
        batch_size: Optional[int] = None,
        seq_len: Optional[int] = None,
    ) -> np.ndarray:
        """
        Generate features (callable interface).

        Args:
            smiles: Single SMILES or list of SMILES
            batch_size: Override batch size
            seq_len: Override sequence length (not used, kept for API compatibility)

        Returns:
            Feature array
        """
        if batch_size is not None:
            self.batch_size = batch_size

        return self.generate(smiles)

    def get_feature_names(self) -> List[str]:
        """Get list of feature names."""
        return self.names

    @property
    def n_features(self) -> int:
        """Number of features generated."""
        return self.nb_features

    def __repr__(self) -> str:
        return (
            f"OnnxBottleneckTransformer("
            f"model='{Path(self.model_path).name}', "
            f"nb_features={self.nb_features})"
        )

    def __getstate__(self):
        """
        Get state for pickling. Exclude the unpicklable ONNX session.
        """
        state = self.__dict__.copy()
        # Remove the unpicklable ONNX session
        state['session'] = None
        state['input_name'] = None
        state['output_name'] = None
        return state

    def __setstate__(self, state):
        """
        Set state when unpickling. Recreate the ONNX session.
        """
        self.__dict__.update(state)
        # Recreate the ONNX session
        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError(
                "ONNX Runtime is required for inference. "
                "Install with: pip install onnxruntime"
            )
        self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
