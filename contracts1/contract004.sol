// SPDX-License-Identifier: Unlicensed

pragma solidity ^0.8.13;
contract additionContract
{
	uint a1 ;
	uint a2 ;

	function setFirst(uint x) private
	{
		a1 = x;
	}

	function setSecond(uint y) private
	{
		a2 = y;
	}

	function addition() view private returns (uint)
	{
		uint res = a1 + a2 ;		
		return res;
	}
}
