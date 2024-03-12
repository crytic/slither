// Resource: https://solodit.xyz/issues/m-10-yaxisvotepowerbalanceof-can-be-manipulated-code4rena-yaxis-yaxis-contest-git

// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

library SafeMath {
    /**
     * @dev Multiplies two numbers, throws on overflow.
     */
    function mul(uint256 a, uint256 b) internal pure returns (uint256 c) {
        if (a == 0) {
            return 0;
        }
        c = a * b;
        assert(c / a == b);
        return c;
    }

    /**
     * @dev Integer division of two numbers, truncating the quotient.
     */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        // assert(b > 0); // Solidity automatically throws when dividing by 0
        // uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold
        return a / b;
    }

    /**
     * @dev Subtracts two numbers, throws on overflow (i.e. if subtrahend is greater than minuend).
     */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        assert(b <= a);
        return a - b;
    }

    /**
     * @dev Adds two numbers, throws on overflow.
     */
    function add(uint256 a, uint256 b) internal pure returns (uint256 c) {
        c = a + b;
        assert(c >= a);
        return c;
    }
}

interface IRewards {
    function balanceOf(address) external view returns (uint256);
    function earned(address) external view returns (uint256);
    function totalSupply() external view returns (uint256);
}
interface IUniswapV2Pair {
    event Approval(address indexed owner, address indexed spender, uint value);
    event Transfer(address indexed from, address indexed to, uint value);

    function name() external pure returns (string memory);
    function symbol() external pure returns (string memory);
    function decimals() external pure returns (uint8);
    function totalSupply() external view returns (uint);
    function balanceOf(address owner) external view returns (uint);
    function allowance(
        address owner,
        address spender
    ) external view returns (uint);

    function approve(address spender, uint value) external returns (bool);
    function transfer(address to, uint value) external returns (bool);
    function transferFrom(
        address from,
        address to,
        uint value
    ) external returns (bool);

    function DOMAIN_SEPARATOR() external view returns (bytes32);
    function PERMIT_TYPEHASH() external pure returns (bytes32);
    function nonces(address owner) external view returns (uint);

    function permit(
        address owner,
        address spender,
        uint value,
        uint deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external;

    event Mint(address indexed sender, uint amount0, uint amount1);
    event Burn(
        address indexed sender,
        uint amount0,
        uint amount1,
        address indexed to
    );
    event Swap(
        address indexed sender,
        uint amount0In,
        uint amount1In,
        uint amount0Out,
        uint amount1Out,
        address indexed to
    );
    event Sync(uint112 reserve0, uint112 reserve1);

    function MINIMUM_LIQUIDITY() external pure returns (uint);
    function factory() external view returns (address);
    function token0() external view returns (address);
    function token1() external view returns (address);
    function getReserves()
        external
        view
        returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
    function price0CumulativeLast() external view returns (uint);
    function price1CumulativeLast() external view returns (uint);
    function kLast() external view returns (uint);

    function mint(address to) external returns (uint liquidity);
    function burn(address to) external returns (uint amount0, uint amount1);
    function swap(
        uint amount0Out,
        uint amount1Out,
        address to,
        bytes calldata data
    ) external;
    function skim(address to) external;
    function sync() external;

    function initialize(address, address) external;
}

interface IVoteProxy {
    function decimals() external pure returns (uint8);
    function totalSupply() external view returns (uint256);
    function balanceOf(address _voter) external view returns (uint256);
}

interface IERC20 {
    event Transfer(address indexed from, address indexed to, uint256 value);

    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 value
    );

    function totalSupply() external view returns (uint256);

    function balanceOf(address account) external view returns (uint256);

    function transfer(address to, uint256 value) external returns (bool);

    function allowance(
        address owner,
        address spender
    ) external view returns (uint256);

    function approve(address spender, uint256 value) external returns (bool);

    function transferFrom(
        address from,
        address to,
        uint256 value
    ) external returns (bool);
}

contract YaxisVotePower is IVoteProxy {
    using SafeMath for uint256;

    // solhint-disable-next-line const-name-snakecase
    uint8 public constant override decimals = uint8(18);

    IUniswapV2Pair public immutable yaxisEthUniswapV2Pair;
    IERC20 public immutable yaxis;
    IRewards public immutable rewardsYaxis;
    IRewards public immutable rewardsYaxisEth;

    constructor(
        address _yaxis,
        address _rewardsYaxis,
        address _rewardsYaxisEth,
        address _yaxisEthUniswapV2Pair
    ) public {
        yaxis = IERC20(_yaxis);
        rewardsYaxis = IRewards(_rewardsYaxis);
        rewardsYaxisEth = IRewards(_rewardsYaxisEth);
        yaxisEthUniswapV2Pair = IUniswapV2Pair(_yaxisEthUniswapV2Pair);
    }

    function totalSupply() external view override returns (uint256) {
        return sqrt(yaxis.totalSupply());
    }

    function balanceOf(
        address _voter
    ) external view override returns (uint256 _balance) {
        uint256 _stakeAmount = rewardsYaxisEth.balanceOf(_voter);
        (uint256 _yaxReserves, , ) = yaxisEthUniswapV2Pair.getReserves();
        uint256 _supply = yaxisEthUniswapV2Pair.totalSupply();
        _supply = _supply == 0 ? 1e18 : _supply;
        uint256 _lpStakingYax = _yaxReserves.mul(_stakeAmount).div(_supply).add(
            rewardsYaxisEth.earned(_voter)
        );
        uint256 _rewardsYaxisAmount = rewardsYaxis.balanceOf(_voter).add(
            rewardsYaxis.earned(_voter)
        );
        _balance = sqrt(
            yaxis.balanceOf(_voter).add(_lpStakingYax).add(_rewardsYaxisAmount)
        );
    }

    function sqrt(uint256 x) private pure returns (uint256 y) {
        uint256 z = (x + 1) / 2;
        y = x;
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
        y = y * (10 ** 9);
    }
}
