# Send to single device.
import json
import web3
from web3 import Web3, HTTPProvider, TestRPCProvider
from solc import compile_source
from web3.contract import ConciseContract

from pyfcm import FCMNotification

push_service = FCMNotification(api_key="AAAACWy09ic:APA91bEuSlYGS7gCO639eZ9qoucmpWQoMuYwqWE1s0K0Of-v4PYPO07uokIHZ9nmyr9Itimnhm5Z2sGONgAHOF1nhyboJD3vzl0F05_TV5BOQjSllL1PXT6Gng-ZIZmJtBjiOQuvCBIt")


# Your api-key can be gotten from:  https://console.firebase.google.com/project/<project-name>/settings/cloudmessaging

# registration_id = "<device registration_id>"
# message_title = "Uber update"
# message_body = "Hi john, your customized news for today is ready"
# result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)

# Send to multiple devices by passing a list of ids.

def push_poll(message_title,registration_ids,message_body=None,data_message=None):
	push_service.multiple_devices_data_message(registration_ids=registration_ids,data_message=data_message)
	result = push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=message_title, message_body="Checkout the update")
	return result

def upvote_push(message_title,registration_id,message_body=None,data_message=None):
	push_service.notify_single_device(registration_id=registration_id,data_message=None)
	result = push_service.single_device_data_message(registration_id=registration_id,data_message=data_message)
	return result

def deploy_contract():

	# Solidity source code
	contract_source_code = '''
	pragma solidity ^0.4.18;
	// We have to specify what version of compiler this code will compile with

	contract Voting {
	  /* mapping field below is equivalent to an associative array or hash.
	  The key of the mapping is candidate name stored as type bytes32 and value is
	  an unsigned integer to store the vote count
	  */
	  struct Voter {
	        bool voted;
	        bytes32 uid;
	    }
	    
	  struct Poll {
	        uint[] options;
	        bytes32[] voterList;
	    }
	    
	  address chairperson;

	  mapping (string => Poll) Polls;
	  mapping (string => Voter) Voters;



	  /* This is the constructor which will be called once when you
	  deploy the contract to the blockchain. When we deploy the contract,
	  we will pass an array of candidates who will be contesting in the election
	  */
	  function Voting() public {
	    chairperson = msg.sender;
	  }
	    
	    
	    function publishPoll(string pollHash,uint _numOptions,bytes32[] voterList)  public returns (bytes32[]) {
	        Polls[pollHash].voterList = voterList;
	        Polls[pollHash].options = new uint[](_numOptions);
	        return Polls[pollHash].voterList;
	  }
	  // This function returns the total votes a candidate has received so far
	  function totalVotesFor(string pollHash) view public returns (uint[]) {
	    // require(validPollHash(pollHash));
	    return Polls[pollHash].options;
	  }

	  // This function increments the vote count for the specified candidate. This
	  // is equivalent to casting a vote
	  function voteForPoll(string pollHash,string voter,uint option) public {
	    // require(validPollHash(pollHash));
	    // require(validVoter(pollHash,voter));
	    Polls[pollHash].options[option] += 1;
	  }

	//   function validVoter(string pollHash,string voter) view public returns (bool) {
	//     for(uint i = 0; i < Polls[pollHash].voterList.length; i++) {
	//       if (keccak256(Polls[pollHash].voterList[i]) == keccak256(voter)) {
	//         return true;
	//       }
	//     }
	//     return false;
	//   }
	//   function validPollHash(string pollHash) view public returns (bool) {
	//       if (Polls[pollHash].options.length != 0) {
	//         return true;
	//       }
	//     return false;
	//   }
	}
		'''

	compiled_sol = compile_source(contract_source_code) # Compiled source code
	contract_interface = compiled_sol['<stdin>:Voting']

	# web3.py instance
	w3 = Web3(HTTPProvider('http://localhost:8545'))

	# Instantiate and deploy contract
	contract = w3.eth.contract(contract_interface['abi'], bytecode=contract_interface['bin'])

	# Get transaction hash from deployed contract
	tx_hash = contract.deploy(transaction={'from': '0x1d36e88A8078F92317aEFf29e691B4aA8eaB7D6f', 'gas': 410000})

	# Get tx receipt to get contract address
	tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
	contract_address = tx_receipt['contractAddress']
	return contract_address
