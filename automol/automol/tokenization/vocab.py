"""
JSON-based vocabulary for SMILES tokenization.

This module provides vocabulary loading without pickle or PyTorch dependencies.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class Vocabulary:
    """
    JSON-based vocabulary for SMILES tokenization.

    This is a pickle-free implementation compatible with the original
    AutoMol vocabulary but loads from JSON format.
    """

    # SMILES tokenization regex pattern
    # Matches: bracketed atoms, two-letter elements, single-letter elements,
    # aromatic atoms, bonds, ring closures, etc.
    SMILES_PATTERN = re.compile(
        r"(\[[^\]]+]|Br?|Cl?|Al|As|Ag|Au|Be|Ba|Bi|Ca|Cu|Fe|Kr|He|Li|Mg|Mn|Na|Ni|Ra|Rb|Si|si|se|Se|Sr|Te|te|Xe|Zn|>>|N|O|S|P|F|I|b|c|n|o|s|p|\(|\)|\.|=|#|-|\+|\\\\|\/|:|~|@|\?|>|\*|\$|\%[0-9]{2}|[0-9])"
    )

    def __init__(self, vocab_path: Optional[str] = None):
        """
        Initialize vocabulary from JSON file.

        Args:
            vocab_path: Path to JSON vocabulary file. If None, uses default.
        """
        if vocab_path is None:
            vocab_path = str(
                Path(__file__).parent.parent / "onnx_models" / "vocab.json"
            )

        self.vocab_path = vocab_path
        self._load_vocab(vocab_path)

    def _load_vocab(self, vocab_path: str) -> None:
        """Load vocabulary from JSON file."""
        with open(vocab_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Token list (index -> token)
        self.tok_list: List[str] = data['tok_list']

        # Token to index mapping
        self.tok2int: Dict[str, int] = data['tok2int']

        # Special indices
        special = data['special_indices']
        self.pad_index: int = special['pad']
        self.unk_index: int = special['unk']
        self.eos_index: int = special['eos']
        self.sos_index: int = special['sos']
        self.mask_index: int = special['mask']
        self.eof_index: int = special['eof']
        self.sof_index: int = special['sof']
        self.cls_index: int = special['cls']
        self.sep_index: int = special['sep']

        # Metadata
        self.metadata: Dict[str, Any] = data.get('metadata', {})

    def __len__(self) -> int:
        """Return vocabulary size."""
        return len(self.tok_list)

    def smile_split(self, smiles: str) -> List[str]:
        """
        Tokenize a SMILES string.

        Args:
            smiles: SMILES string to tokenize

        Returns:
            List of tokens
        """
        if smiles is None:
            return []

        tokens = self.SMILES_PATTERN.findall(smiles)

        # Verify tokenization is lossless
        reconstructed = ''.join(tokens)
        if reconstructed != smiles:
            # If tokenization fails, return empty (will be handled as unknown)
            return []

        return tokens

    def smile2int(
        self,
        smiles: str,
        max_smile_len: Optional[int] = None,
        with_eos: bool = False,
        with_sos: bool = False,
        return_len: bool = False,
    ) -> List[int] | Tuple[List[int], int]:
        """
        Convert SMILES to integer token indices.

        Args:
            smiles: SMILES string to convert
            max_smile_len: Maximum sequence length (will pad/truncate)
            with_eos: Whether to add end-of-sequence token
            with_sos: Whether to add start-of-sequence token
            return_len: Whether to return original sequence length

        Returns:
            List of integer indices (and optionally original length)
        """
        tokens = self.smile_split(smiles)
        seq = [self.tok2int.get(tok, self.unk_index) for tok in tokens]

        if with_eos:
            seq.append(self.eos_index)
        if with_sos:
            seq = [self.sos_index] + seq

        origin_seq_len = len(seq)

        if max_smile_len is not None:
            if len(seq) <= max_smile_len:
                # Pad sequence
                seq = seq + [self.pad_index] * (max_smile_len - len(seq))
            else:
                # Truncate sequence
                seq = seq[:max_smile_len]

        if return_len:
            return seq, origin_seq_len
        return seq

    def int2smiles(self, seq: List[int]) -> str:
        """
        Convert integer token indices back to SMILES.

        Args:
            seq: List of integer token indices

        Returns:
            Reconstructed SMILES string
        """
        tokens = []
        for idx in seq:
            if idx == self.eos_index:
                break
            elif idx in [self.sos_index, self.pad_index, self.cls_index]:
                continue
            elif idx in [self.mask_index, self.unk_index]:
                tokens.append(self.tok_list[idx])
            else:
                if 0 <= idx < len(self.tok_list):
                    tokens.append(self.tok_list[idx])

        return "".join(tokens)

    def get_token(self, index: int) -> str:
        """Get token string for given index."""
        if 0 <= index < len(self.tok_list):
            return self.tok_list[index]
        return self.tok_list[self.unk_index]

    def get_index(self, token: str) -> int:
        """Get index for given token string."""
        return self.tok2int.get(token, self.unk_index)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vocabulary":
        """
        Create vocabulary from dictionary.

        Args:
            data: Dictionary with tok_list, tok2int, special_indices

        Returns:
            Vocabulary instance
        """
        vocab = object.__new__(cls)
        vocab.tok_list = data['tok_list']
        vocab.tok2int = data['tok2int']

        special = data['special_indices']
        vocab.pad_index = special['pad']
        vocab.unk_index = special['unk']
        vocab.eos_index = special['eos']
        vocab.sos_index = special['sos']
        vocab.mask_index = special['mask']
        vocab.eof_index = special['eof']
        vocab.sof_index = special['sof']
        vocab.cls_index = special['cls']
        vocab.sep_index = special['sep']

        vocab.metadata = data.get('metadata', {})
        vocab.vocab_path = None

        return vocab

    def to_dict(self) -> Dict[str, Any]:
        """Convert vocabulary to dictionary."""
        return {
            'tok_list': self.tok_list,
            'tok2int': self.tok2int,
            'special_indices': {
                'pad': self.pad_index,
                'unk': self.unk_index,
                'eos': self.eos_index,
                'sos': self.sos_index,
                'mask': self.mask_index,
                'eof': self.eof_index,
                'sof': self.sof_index,
                'cls': self.cls_index,
                'sep': self.sep_index,
            },
            'metadata': self.metadata,
        }
