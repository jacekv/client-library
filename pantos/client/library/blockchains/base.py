"""Base classes for all blockchain clients and errors.

"""
import abc
import dataclasses
import typing

import semantic_version  # type: ignore
from pantos.common.blockchains.base import Blockchain
from pantos.common.blockchains.base import BlockchainHandler
from pantos.common.blockchains.base import BlockchainUtilities
from pantos.common.blockchains.base import BlockchainUtilitiesError
from pantos.common.blockchains.base import VersionedContractAbi
from pantos.common.blockchains.enums import ContractAbi
from pantos.common.blockchains.factory import get_blockchain_utilities
from pantos.common.blockchains.factory import initialize_blockchain_utilities
from pantos.common.entities import ServiceNodeBid
from pantos.common.exceptions import ErrorCreator
from pantos.common.types import AccountId
from pantos.common.types import BlockchainAddress
from pantos.common.types import PrivateKey

from pantos.client.library.configuration import get_blockchain_config
from pantos.client.library.exceptions import ClientLibraryError

_CONTRACTS_VERSION = semantic_version.Version('1.0.0')

VERSIONED_CONTRACT_ABIS = {
    contract_abi: VersionedContractAbi(contract_abi, _CONTRACTS_VERSION)
    for contract_abi in ContractAbi
}


class BlockchainClientError(ClientLibraryError):
    """Base exception class for all blockchain client errors.

    """
    pass


class BlockchainClient(BlockchainHandler, ErrorCreator[BlockchainClientError]):
    """Base class for all blockchain clients.

    """
    def __init__(self):
        """Construct a blockchain client instance.

        Raises
        ------
        BlockchainClientError
            If the blockchain is not active in the configuration or if
            the corresponding blockchain utilities cannot be
            initialized.

        """
        if not self._get_config()['active']:
            raise self._create_error('blockchain is not active')
        blockchain_node_url = self._get_config()['provider']
        fallback_blockchain_nodes_urls = self._get_config().get(
            'fallback_providers', [])
        average_block_time = self._get_config()['average_block_time']
        required_transaction_confirmations = self._get_config(
        )['confirmations']
        transaction_network_id = self._get_config().get('chain_id')

        try:
            initialize_blockchain_utilities(
                self.get_blockchain(), [blockchain_node_url],
                fallback_blockchain_nodes_urls, average_block_time,
                required_transaction_confirmations, transaction_network_id)
        except BlockchainUtilitiesError:
            raise self._create_error(
                'unable to initialize the {} utilities'.format(
                    self.get_blockchain_name()))

    @dataclasses.dataclass
    class ComputeTransferSignatureRequest:
        """Request data for computing the sender's signature for a
        single-chain token transfer.

        Attributes
        ----------
        sender_private_key : PrivateKey
            The unencrypted private key of the sender's account.
        recipient_address : BlockchainAddress
            The address of the recipient's account.
        token_address : BlockchainAddress
            The transferred token's blockchain address.
        token_amount : int
            The transferred token amount (in 10^-d units, where d is the
            token's number of decimals).
        service_node_address : BlockchainAddress
            The address of the service node used for the token transfer.
        service_node_bid : ServiceNodeBid
            The service node bid used for the token transfer.
        valid_until : int
            The timestamp until when the token transfer is valid (in
            seconds since the epoch).

        """
        sender_private_key: PrivateKey
        recipient_address: BlockchainAddress
        token_address: BlockchainAddress
        token_amount: int
        service_node_address: BlockchainAddress
        service_node_bid: ServiceNodeBid
        valid_until: int

    @dataclasses.dataclass
    class ComputeTransferSignatureResponse:
        """Response data for computing the sender's signature for a
        single-chain token transfer.

        Attributes
        ----------
        sender_address : BlockchainAddress
            The address of the sender's account.
        sender_nonce : int
            The unique nonce of the sender for the token transfer.
        signature : str
            The sender's token transfer signature.

        """
        sender_address: BlockchainAddress
        sender_nonce: int
        signature: str

    @abc.abstractmethod
    def compute_transfer_signature(
            self, request: ComputeTransferSignatureRequest) \
            -> ComputeTransferSignatureResponse:  # pragma: no cover
        """Compute the sender's signature for a single-chain token
        transfer.

        Parameters
        ----------
        request : ComputeTransferSignatureRequest
            The request data for computing the transfer signature.

        Returns
        -------
        ComputeTransferSignatureResponse
            The response data with the computed transfer signature.

        Raises
        ------
        BlockchainClientError
            If the signature for the token transfer cannot be computed.

        """
        pass

    @dataclasses.dataclass
    class ComputeTransferFromSignatureRequest:
        """Request data for computing the sender's signature for a
        cross-chain token transfer.

        Attributes
        ----------
        destination_blockchain : Blockchain
            The token transfer's destination blockchain.
        sender_private_key : PrivateKey
            The unencrypted private key of the sender's account on the
            source blockchain.
        recipient_address : BlockchainAddress
            The address of the recipient's account on the destination
            blockchain.
        source_token_address : BlockchainAddress
            The transferred token's address on the source blockchain.
        destination_token_address : BlockchainAddress
            The transferred token's address on the destination
            blockchain.
        token_amount : int
            The transferred token amount (in 10^-d units, where d is the
            token's number of decimals).
        service_node_address : BlockchainAddress
            The address of the service node used for the token transfer.
        service_node_bid : ServiceNodeBid
            The service node bid used for the token transfer.
        valid_until : int
            The timestamp until when the token transfer is valid (in
            seconds since the epoch).

        """
        destination_blockchain: Blockchain
        sender_private_key: PrivateKey
        recipient_address: BlockchainAddress
        source_token_address: BlockchainAddress
        destination_token_address: BlockchainAddress
        token_amount: int
        service_node_address: BlockchainAddress
        service_node_bid: ServiceNodeBid
        valid_until: int

    @dataclasses.dataclass
    class ComputeTransferFromSignatureResponse:
        """Response data for computing the sender's signature for a
        cross-chain token transfer.

        Attributes
        ----------
        sender_address : BlockchainAddress
            The address of the sender's account on the source
            blockchain.
        sender_nonce : int
            The unique nonce of the sender for the token transfer on the
            source blockchain.
        signature : str
            The sender's token transfer signature.

        """
        sender_address: BlockchainAddress
        sender_nonce: int
        signature: str

    @abc.abstractmethod
    def compute_transfer_from_signature(
            self, request: ComputeTransferFromSignatureRequest) \
            -> ComputeTransferFromSignatureResponse:  # pragma: no cover
        """Compute the sender's signature for a cross-chain token
        transfer.

        Parameters
        ----------
        request : ComputeTransferFromSignatureRequest
            The request data for computing the transfer signature.

        Returns
        -------
        ComputeTransferFromSignatureResponse
            The response data with the computed transfer signature.

        Raises
        ------
        BlockchainClientError
            If the signature for the token transfer cannot be computed.

        """
        pass

    @abc.abstractmethod
    def is_valid_recipient_address(
            self, recipient_address: str) -> bool:  # pragma: no cover
        """Determine if an address string is a valid recipient address
        on the blockchain.

        Parameters
        ----------
        recipient_address : str
            The address string to check.

        Returns
        -------
        bool
            True if the given address string is a valid recipient
            address on the blockchain.

        """
        pass

    def decrypt_private_key(self, keystore: str, password: str) -> PrivateKey:
        """Decrypt the private key from a password-encrypted keystore.

        Parameters
        ----------
        keystore : str
            The keystore contents.
        password : str
            The password to decrypt the private key.

        Returns
        -------
        PrivateKey
            The decrypted private key.

        Raises
        ------
        BlockchainClientError
            If the private key cannot be loaded from the keystore file.

        """
        try:
            return PrivateKey(self._get_utilities().decrypt_private_key(
                keystore, password))
        except Exception:
            raise self._create_error(
                'unable to load a private key from a keystore',
                keystore=keystore)

    @abc.abstractmethod
    def read_external_token_address(
        self, token_address: BlockchainAddress,
        destination_blockchain: Blockchain
    ) -> BlockchainAddress:  # pragma: no cover
        """Read an external token address that is registered at the
        Pantos Hub on the blockchain.

        Parameters
        ----------
        token_address : BlockchainAddress
            The (native) blockchain address of the token.
        destination_blockchain : Blockchain
            The blockchain to read the token's external address for.

        Returns
        -------
        BlockchainAddress
            The external blockchain address of the token.

        Raises
        ------
        BlockchainClientError
            If the external token address cannot be read or if it is not
            active.

        """
        pass

    @abc.abstractmethod
    def read_service_node_addresses(
            self) -> typing.List[BlockchainAddress]:  # pragma: no cover
        """Read the blockchain addresses of the active service nodes
        registered at the Pantos Hub on the blockchain.

        Returns
        -------
        list of BlockchainAddress
            The blockchain addresses of the active service nodes.

        Raises
        ------
        BlockchainClientError
            If the blockchain adresses of the active service nodes
            cannot be read.

        """
        pass

    @abc.abstractmethod
    def read_service_node_url(
            self, service_node_address: BlockchainAddress
    ) -> str:  # pragma: no cover
        """Read a service node's URL that is registered at the Pantos
        Hub on the blockchain.

        Parameters
        ----------
        service_node_address : BlockchainAddress
            The blockchain address of the service node.

        Returns
        -------
        str
            The service node's registered URL.

        Raises
        ------
        BlockchainClientError
            If the service node's registered URL cannot be read or if
            the service node is not active.

        """
        pass

    def read_token_balance(self, token_address: BlockchainAddress,
                           account_id: AccountId) -> int:
        """Read a blockchain account's balance of a Pantos-compatible
        token.

        Parameters
        ----------
        token_address : BlockchainAddress
            The blockchain address of the token.
        account_id : AccountId
            The identifier of the blockchain account.

        Returns
        -------
        int
            The blockchain account's token balance in the token's
            smallest subunit.

        Raises
        ------
        BlockchainClientError
            If the blockchain account's token balance cannot be read.

        """
        try:
            account_address = self._account_id_to_account_address(account_id)
            return self._get_utilities().get_balance(
                account_address, token_address=token_address)
        except Exception:
            raise self._create_error(
                'unable to read the token balance of a blockchain account',
                token_address=token_address, account_id=account_id)

    @abc.abstractmethod
    def read_token_decimals(
            self, token_address: BlockchainAddress) -> int:  # pragma: no cover
        """Read the number of decimals of a Pantos-compatible token.

        Parameters
        ----------
        token_address : BlockchainAddress
            The blockchain address of the token.

        Returns
        -------
        int
            The number of decimals of the token.

        Raises
        ------
        BlockchainClientError
            If the token's number of decimals cannot be read.

        """
        pass

    def _account_id_to_account_address(
            self, account_id: AccountId) -> BlockchainAddress:
        if isinstance(account_id, BlockchainAddress):
            return account_id
        return BlockchainAddress(self._get_utilities().get_address(account_id))

    def _get_config(self) -> typing.Dict[str, typing.Any]:
        return get_blockchain_config(self.get_blockchain())

    def _get_utilities(self) -> BlockchainUtilities:
        return get_blockchain_utilities(self.get_blockchain())
