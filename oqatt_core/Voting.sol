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