import blockchain
from blockchain.block import Block
from blockchain.util import nonempty_intersection
import hashlib

class PoWBlock(Block):
    """ Extends Block, adding proof-of-work primitives. """

    def seal_is_valid(self):
        """ Checks whether a block's seal_data forms a valid seal.
            In PoW, this means that H(block) <= target
Hi Jennifer - I'm a MBA student at Cornell (go big red!) and am very interested in a number of roles listed at the Google Boulder office. I was curious if you would be open to chatting about your experience at Google/tech in Boulder? Either way, I'd love to connect for future endeavours!
Jonathan
            Returns:
                bool: True only if a block's seal data forms a valid seal according to PoW.
        """
        return int(self.hash, 16) <= self.target

    def get_weight(self):
        """ Gets the approximate total amount of work that has gone into making a block.
            The consensus weight of a block is how much harder a block is to mine
            than the easiest possible block, with a target of 2^256.
            e.g. a block with weight 4 will take 4 times longer on expectation to mine than
            a block carrying target 2^256.
        

        Returns:
            int: The consensus weight of a block.
        """
        #weight = self.target/(2^256)
        if self.target > 0:
            
            weight = int((2**256)/(self.target))
        elif self.target == 0 :
            weight = int(2**256)
        # Placeholder for (1a)
        return weight

    def mine(self):
        """ PoW mining loop; attempts to seal a block with new seal data until the seal is valid
            (performing brute-force mining).  Terminates once block is valid.
        """
        nonce = 0
        while not self.seal_is_valid():
            self.set_seal_data(nonce)
            nonce += 1

    def calculate_appropriate_target(self):
        """ For simplicity, we will just keep a constant target / difficulty
        for now; in real cryptocurrencies, the target adjusts based on some
        formula based on the parent's target, and the difference in timestamps
        between blocks  indicating mining is too slow or quick. """
        if self.parent_hash == "genesis":
            return int(2 ** 248)
        return blockchain.chain.blocks[self.parent_hash].target
