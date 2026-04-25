# @version ^0.4.0

"""
@title ArcCardsReceiver
@notice Escrow contract for Agentic Virtual Card payments on Arc Network.
@dev Uses Native USDC (6 decimals) and order_id mapping for fulfillment.
"""

from ethereum.ercs import IERC20

# Events
event PaymentReceived:
    order_id: indexed(bytes32)
    sender: indexed(address)
    amount: uint256
    timestamp: uint256

event Withdrawal:
    recipient: indexed(address)
    amount: uint256

# Storage
USDC: public(address)
owner: public(address)
treasury: public(address)
is_paid: public(HashMap[bytes32, bool])

@deploy
def __init__(_usdc_address: address, _treasury: address):
    self.USDC = _usdc_address
    self.owner = msg.sender
    self.treasury = _treasury

@external
def pay_for_order(order_id: bytes32, amount: uint256):
    """
    @notice Agents call this to pay for their virtual card.
    @param order_id Unique order ID from the backend.
    @param amount Amount in USDC (6 decimals).
    """
    assert not self.is_paid[order_id], "Order already paid"
    assert amount > 0, "Amount must be > 0"
    
    # Transfer USDC from sender to this contract
    # Requires previous approve() call from agent
    success: bool = extcall IERC20(self.USDC).transferFrom(msg.sender, self, amount)
    assert success, "USDC Transfer Failed"
    
    self.is_paid[order_id] = True
    log PaymentReceived(order_id=order_id, sender=msg.sender, amount=amount, timestamp=block.timestamp)

@external
def withdraw(amount: uint256):
    """
    @notice Admin function to move funds to treasury.
    """
    assert msg.sender == self.owner, "Only owner"
    success: bool = extcall IERC20(self.USDC).transfer(self.treasury, amount)
    assert success, "Withdrawal Failed"
    log Withdrawal(recipient=self.treasury, amount=amount)

@external
def set_treasury(_new_treasury: address):
    assert msg.sender == self.owner, "Only owner"
    self.treasury = _new_treasury

@external
def transfer_ownership(_new_owner: address):
    assert msg.sender == self.owner, "Only owner"
    self.owner = _new_owner

@view
@external
def check_order_status(order_id: bytes32) -> bool:
    return self.is_paid[order_id]
