from abc import ABC, abstractmethod # We want to make Block an abstract class; either a PoW or PoA block
import blockchain
from blockchain.util import sha256_2_string, encode_as_str
import time
import persistent
from blockchain.util import nonempty_intersection

class Block(ABC, persistent.Persistent):

    def __init__(self, height, transactions, parent_hash, is_genesis=False):
        """ Creates a block template (unsealed).

        Args:
            height (int): height of the block in the chain (# of blocks between block and genesis).
            transactions (:obj:`list` of :obj:`Transaction`): ordered list of transactions in the block.
            parent_hash (str): the hash of the parent block in the blockchain.
            is_genesis (bool, optional): True only if the block is a genesis block.

        Attributes:
            parent_hash (str): the hash of the parent block in blockchain.
            height (int): height of the block in the chain (# of blocks between block and genesis).
            transactions (:obj:`list` of :obj:`Transaction`): ordered list of transactions in the block.
            timestamp (int): Unix timestamp of the block
            target (int): Target value for the block's seal to be valid (different for each seal mechanism)
            is_genesis (bool): True only if the block is a genesis block (first block in the chain).
            merkle (str): Merkle hash of the list of transactions in a block, uniquely identifying the list.
            seal_data (int): Seal data for block (in PoW this is the nonce satisfying the PoW puzzle; in PoA, the signature of the authority"
            hash (str): Hex-encoded SHA256^2 hash of the block header (self.header())
        """
        self.parent_hash = parent_hash
        self.height = height
        self.transactions = transactions
        self.timestamp = int(time.time())
        self.target = self.calculate_appropriate_target()
        self.is_genesis = is_genesis
        self.merkle = self.calculate_merkle_root()
        self.seal_data = 0 # temporarily set seal_data to 0
        self.hash = self.calculate_hash() # keep track of hash for caching purposes

    def calculate_merkle_root(self):
        hash_trans = [sha256_2_string(str(x)) for x in self.transactions]

        if len(hash_trans) == 0:
            hash_trans = sha256_2_string("")

        while len(hash_trans) > 1:
        	
        	i=0
        	hash_trans_nex = []

        	while i < len(hash_trans):
        		if i ==  len(hash_trans) - 1:
        			hash_trans_nex.append((hash_trans[i]))
        		
        		else:
        			hash_trans_nex.append(sha256_2_string(hash_trans[i] + hash_trans[i + 1]))
        			i += 1
        		i += 1
        	hash_trans = hash_trans_nex

        return hash_trans[0]

    def unsealed_header(self):
        """ Computes the header string of a block (the component that is sealed by mining).

        Returns:
            str: String representation of the block header without the seal.
        """
        return encode_as_str([self.height, self.timestamp, self.target, self.parent_hash, self.is_genesis, self.merkle], sep='`')

    def header(self):
        """ Computes the full header string of a block after mining (includes the seal).

        Returns:
            str: String representation of the block header.
        """
        return encode_as_str([self.unsealed_header(), self.seal_data], sep='`')

    def calculate_hash(self):
        """ Get the SHA256^2 hash of the block header.

        Returns:
            str: SHA256^2 hash of self.header()
        """
        return sha256_2_string(str(self.header()))

    def __repr__(self):
        """ Get a full representation of a block as string, for debugging purposes; includes all transactions.

        Returns:
            str: Full and unique representation of a block and its transactions.
        """
        return encode_as_str([self.header(), "!".join([str(tx) for tx in self.transactions])], sep="`")

    def set_seal_data(self, seal_data):
        """ Adds seal data to a block, recomputing the block's hash for its changed header representation.
        This method should never be called after a block is added to the blockchain!

        Args:
            seal_data (int): The seal data to set.
        """
        self.seal_data = seal_data
        self.hash = self.calculate_hash()

    def is_valid(self):
        """ Check whether block is fully valid according to block rules.

        Includes checking for no double spend, that all transactions are valid, that all header fields are correctly
        computed, etc.

        Returns:
            bool, str: True if block is valid, False otherwise plus an error or success message.
        """

        chain = blockchain.chain # This object of type Blockchain may be useful

        # (checks that apply to all blocks)

        #[test_rejects_invalid_merkle]
        #Check if the current block's merkle root is the same as the calculated mr
        if self.merkle != self.calculate_merkle_root():
            return False, "Merkle root failed to match"

        #[test_rejects_invalid_hash]
        #Check if the current block's hash is the same as the calculated hash of the block
        if self.hash != self.calculate_hash():
            return False, "Hash failed to match"

        #[test_rejects_too_many_txs]
        #Check to see if the current block meets the transaction limit
        if len(self.transactions)>900:
            return False, "Too many transactions"
        

        # (checks that apply to genesis block)
            # Check that height is 0 and parent_hash is "genesis" [test_invalid_genesis]
            # On failure: return False, "Invalid genesis"
            
        #[test_invalid_genesis]
        #Chek if the current block is genesis or not
        if self.is_genesis is True:

            #Make sure that this is a valid genesis block
            #Check that it is at height 0 and that the parent hash is genesis
            if self.height != 0 or self.parent_hash != "genesis":
                return False, "Invalid genesis"

        # (checks that apply only to non-genesis blocks)
            # Check that parent exists (you may find chain.blocks helpful) [test_nonexistent_parent]
            # On failure: return False, "Nonexistent parent"

        # (checks that apply only to non-genesis blocks)
        if self.is_genesis is False:

            #[test_nonexistent_parent]
            #Check that the parent block is in the current chain
            if self.parent_hash not in chain.blocks: 
                return False, "Nonexistent parent"

            #[test_bad_height]
            #Check if the space between the current block and parent block is 1
            if (self.height - chain.blocks[self.parent_hash].height) != 1:
                return False, "Invalid height"
            
            #[test_bad_timestamp]
            #Check that the timestamp on the block and parent block are the same
            if self.timestamp != chain.blocks[self.parent_hash].timestamp:
                return False, "Invalid timestamp"
            

            #[test_bad_seal]
            #Check that the seal is valid
            if not self.seal_is_valid():
                return False, "Invalid seal"

            #[test_malformed_txs]
            #get each transaction in the block
            for i in self.transactions:
                #Check if the transaction is valid
                if not i.is_valid():
                    return False, "Malformed transaction included"

            
                # the transaction has not already been included on a block on the same blockchain as this block [test_double_tx_inclusion_same_chain]
                # (or twice in this block; you will have to check this manually) [test_double_tx_inclusion_same_block]
                # (you may find chain.get_chain_ending_with (list of all blocks in the chain between desired block and genesis.) and chain.blocks_containing_tx (Maps transaction hashes to all blocks in the DB that spent them as list of their hashes.) and util.nonempty_intersection useful(turns true iff two lists have a nonempty intersection.))
                # On failure: return False, "Double transaction inclusion"

            #initiate lists for later checks
            l=[]
            output=[]
            
            # Check that for every transaction
            for tx in self.transactions: 
                #create a list of transactions
                l.append(tx)

                #[test_double_tx_inclusion_same_chain]
                #check that the transaction hash is not already presenet in the chain
                if tx.hash in chain.blocks_containing_tx:
                    return False, "Double transaction inclusion"

                #[test_double_tx_inclusion_same_block]
                #Check that the transaction doesnt appear twice in the same block
                if self.transactions.count(tx) != 1:
                    return False, "Double transaction inclusion"


                #for money creation test
                in_total = 0
                
                # get the input ref for each tx
                for input_ref in tx.input_refs:

                    # Split the input ref into the hash and transaction position
                    h, pos = input_ref.split(':')
                    #convert position to int for later use
                    pos = int(pos)
        
                    #[test_failed_input_lookup]
                    #Create a list of transaction hashes in the block
                    tx_h = [tx.hash for tx in self.transactions]

        
                    #Check if the input ref hash is in the chain                    
                    if h not in chain.all_transactions:
                        #If input ref hash is not in the chan, check if its in the block
                        if h not in tx_h:
                            return False, "Required output not found"

                    #Check if the input ref hash is in the chain 
                    if h in chain.all_transactions:
                        #create variable with list of transaction from input ref hash
                        input_tx = chain.all_transactions[h]

                    #Check if the input ref hash is not in the chain 
                    else:
                        #Get each transaction in the block
                        for input_trans in self.transactions:
                            #if the input ref hash is equal to the hash of a transaction in the block
                            if h == input_trans.hash:
                                #if true, set the input tx var to the transaction from the block and exit
                                input_tx = input_trans
                                break

                    #Get the number of outputs in the transaction
                    output_num = len(input_tx.outputs)

                    #check if the 
                    if pos >= output_num:
                        return False, "Required output not found"

                    
                    #[test_user_consistency]
                    # Get user who received transaction input
                    rec = input_tx.outputs[pos].receiver

                    # list of users the sent transaction
                    send= [user.sender for user in tx.outputs]

                    # Get user in send list
                    for user in send:
                        #check if user is the reciever
                        if user != rec:
                            return False, "User inconsistencies"
                
                    #[test_doublespent_input_same_chain]
                    #Check if trans input ref has been spent elsewhere in the chain
                    if input_ref in chain.blocks_spending_input:

                        #get a list of blocks to check
                        blks = chain.get_chain_ending_with(self.parent_hash)

                        #get a list of blocks where the input ref was spent
                        spend = chain.blocks_spending_input[input_ref]

                        #check if the block the input ref was spent on was spent elsewhere on the chain
                        if nonempty_intersection(blks, spend):
                            return False, "Double-spent input"

                    #[test_doublespent_input_same_block]
                    #compile tx inputs on block
                    b_inputs = []
                    for trans in self.transactions:
                        #for each tx in block
                        for tx_input_ref in trans.input_refs:
                            #for each inport ref in the tx, add to list
                            b_inputs.append(tx_input_ref)

                    # check if the input was already spent on the block
                    if b_inputs.count(input_ref) != 1:
                        return False, "Double-spent input"

                    #[test_input_txs_on_chain]
                    #check if the transaction is on the current blockchain

                    if h in chain.blocks_containing_tx:
                        #create list of blocks in question and blocks that contain the input transaction
                        blks = chain.get_chain_ending_with(self.parent_hash)
                        b_w_h = chain.blocks_containing_tx[h]

                        #check if the input trans is in both lists
                        if not nonempty_intersection(blks, b_w_h):
                            #check if the input transaction is not in the transactions on block
                            if h not in tx_h:
                                return False, "Input transaction not found"
#FIX THIS
                    #[test_input_txs_in_block]
                    #if the input ref hash is not on the chain, check if its in the current block
                    
                    elif h in tx_h:
                        break
                    else:
                        return False, "Input transaction not found"
                    
                        
                    #for money creation test                        
                    in_total += input_tx.outputs[pos].amount

                #[test_user_consistency]
                #create a list of senders of transaxctions
                send=[]
                for user in tx.outputs:
                    send.append(user.sender)

                #check if there is only one sender
                if len(set(send)) > 1:
                    return False, "User inconsistencies"

                #[test_no_money_creation]
                #create a list of transactions to calculate amount
                out_total=[]
                for output in tx.outputs:
                    out_total.append(output.amount)

                #get the total output amount    
                out_total = sum(out_total)
                
                #check if the output value is greater than the input value
                if in_total<out_total:
                    return False, "Creating money"

        return True, "All checks passed"


    # ( these just establish methods for subclasses to implement; no need to modify )
    @abstractmethod
    def get_weight(self):
        """ Should be implemented by subclasses; gives consensus weight of block. """
        pass

    @abstractmethod
    def calculate_appropriate_target(self):
        """ Should be implemented by subclasses; calculates correct target to use in block. """
        pass

    @abstractmethod
    def seal_is_valid(self):
        """ Should be implemented by subclasses; returns True iff the seal_data creates a valid seal on the block. """
        pass
