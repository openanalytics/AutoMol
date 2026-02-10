"""
SMILES tokenizer for batch processing.

Provides utilities for tokenizing batches of SMILES strings for
neural network input.
"""

import numpy as np
from typing import List, Optional, Union

from .vocab import Vocabulary


class SmilesTokenizer:
    """
    Batch tokenizer for SMILES strings.

    Handles conversion of SMILES strings to integer tensors
    suitable for transformer models.
    """

    def __init__(
        self,
        vocab: Optional[Vocabulary] = None,
        vocab_path: Optional[str] = None,
        max_seq_len: int = 220,
        add_sos: bool = True,
        add_eos: bool = True,
    ):
        """
        Initialize the tokenizer.

        Args:
            vocab: Vocabulary instance to use
            vocab_path: Path to vocabulary JSON (used if vocab is None)
            max_seq_len: Maximum sequence length
            add_sos: Whether to add start-of-sequence token
            add_eos: Whether to add end-of-sequence token
        """
        if vocab is not None:
            self.vocab = vocab
        else:
            self.vocab = Vocabulary(vocab_path)

        self.max_seq_len = max_seq_len
        self.add_sos = add_sos
        self.add_eos = add_eos

    @property
    def pad_index(self) -> int:
        """Return the padding token index."""
        return self.vocab.pad_index

    @property
    def vocab_size(self) -> int:
        """Return the vocabulary size."""
        return len(self.vocab)

    def tokenize_single(self, smiles: str) -> List[int]:
        """
        Tokenize a single SMILES string.

        Args:
            smiles: SMILES string

        Returns:
            List of integer token indices
        """
        return self.vocab.smile2int(
            smiles,
            max_smile_len=self.max_seq_len,
            with_eos=self.add_eos,
            with_sos=self.add_sos,
        )

    def tokenize_batch(
        self,
        smiles_list: List[str],
        return_lengths: bool = False,
    ) -> Union[np.ndarray, tuple]:
        """
        Tokenize a batch of SMILES strings.

        Args:
            smiles_list: List of SMILES strings
            return_lengths: Whether to return original sequence lengths

        Returns:
            numpy array of shape [seq_len, batch_size] (for transformer input)
            Optionally also returns list of original lengths
        """
        batch_tokens = []
        lengths = []

        for smiles in smiles_list:
            if return_lengths:
                tokens, length = self.vocab.smile2int(
                    smiles,
                    max_smile_len=self.max_seq_len,
                    with_eos=self.add_eos,
                    with_sos=self.add_sos,
                    return_len=True,
                )
                lengths.append(length)
            else:
                tokens = self.vocab.smile2int(
                    smiles,
                    max_smile_len=self.max_seq_len,
                    with_eos=self.add_eos,
                    with_sos=self.add_sos,
                )
            batch_tokens.append(tokens)

        # Convert to numpy array: [batch_size, seq_len]
        arr = np.array(batch_tokens, dtype=np.int64)

        # Transpose to [seq_len, batch_size] for transformer input
        arr = arr.T

        if return_lengths:
            return arr, lengths
        return arr

    def decode_single(self, tokens: List[int]) -> str:
        """
        Decode token indices back to SMILES.

        Args:
            tokens: List of integer token indices

        Returns:
            SMILES string
        """
        return self.vocab.int2smiles(tokens)

    def decode_batch(self, tokens: np.ndarray) -> List[str]:
        """
        Decode a batch of token arrays back to SMILES.

        Args:
            tokens: numpy array of shape [seq_len, batch_size]

        Returns:
            List of SMILES strings
        """
        # Transpose back to [batch_size, seq_len]
        tokens = tokens.T

        return [self.decode_single(row.tolist()) for row in tokens]

    def get_padding_mask(self, tokens: np.ndarray) -> np.ndarray:
        """
        Generate padding mask for transformer attention.

        Args:
            tokens: Token array of shape [seq_len, batch_size]

        Returns:
            Boolean mask of shape [batch_size, seq_len] where True indicates padding
        """
        # Transpose to [batch_size, seq_len]
        tokens_t = tokens.T
        return tokens_t == self.pad_index

    def __call__(
        self,
        smiles: Union[str, List[str]],
        return_lengths: bool = False,
    ) -> Union[np.ndarray, tuple]:
        """
        Tokenize SMILES string(s).

        Args:
            smiles: Single SMILES or list of SMILES
            return_lengths: Whether to return original lengths

        Returns:
            Token array(s)
        """
        if isinstance(smiles, str):
            smiles = [smiles]

        return self.tokenize_batch(smiles, return_lengths=return_lengths)
