"""星屑占卜 最优策略求解器（精确期望值搜索）

规则：3x3 格子随机放 1-9 不重复数字，系统先翻开 1 格；
玩家再手动翻 3 格（共 4 格可见），然后选一条线（3 行 / 3 列 / 2 对角线），
三个数之和按 PAYOUT 表换星砂。

格子编号（行优先）:
    0 1 2
    3 4 5
    6 7 8
"""
from functools import lru_cache
from itertools import permutations

PAYOUT = {
    6: 500, 7: 500, 8: 150, 9: 100, 10: 50, 11: 30, 12: 20, 13: 20, 14: 10,
    15: 10, 16: 10, 17: 20, 18: 20, 19: 30, 20: 50, 21: 100, 22: 150,
    23: 500, 24: 500,
}

# 线的名字与界面上箭头对应
LINES = {
    "row0": (0, 1, 2), "row1": (3, 4, 5), "row2": (6, 7, 8),
    "col0": (0, 3, 6), "col1": (1, 4, 7), "col2": (2, 5, 8),
    "diag": (0, 4, 8),       # 左上 → 右下（左上角箭头）
    "anti": (6, 4, 2),       # 左下 → 右上（左下角箭头）
}


def _key(known):
    return tuple(known.get(i, 0) for i in range(9))


@lru_cache(maxsize=None)
def line_ev(state, line):
    """state: 9 元组，0 表示未知。返回这条线的期望星砂。"""
    used = {v for v in state if v}
    remaining = [v for v in range(1, 10) if v not in used]
    known_sum = sum(state[i] for i in line if state[i])
    k = sum(1 for i in line if not state[i])
    if k == 0:
        return float(PAYOUT[known_sum])
    total = n = 0
    for combo in permutations(remaining, k):
        total += PAYOUT[known_sum + sum(combo)]
        n += 1
    return total / n


def best_line(state):
    state = tuple(state)
    return max(((name, line_ev(state, cells)) for name, cells in LINES.items()),
               key=lambda x: x[1])


@lru_cache(maxsize=None)
def state_ev(state):
    """从当前状态出发、按最优策略继续的期望星砂。"""
    revealed = sum(1 for v in state if v)
    if revealed >= 4:
        return best_line(state)[1]
    return max(_reveal_ev(state, c) for c in range(9) if not state[c])


def _reveal_ev(state, cell):
    used = {v for v in state if v}
    remaining = [v for v in range(1, 10) if v not in used]
    total = 0.0
    for v in remaining:
        s = list(state)
        s[cell] = v
        total += state_ev(tuple(s))
    return total / len(remaining)


def best_reveal(state):
    """返回 (应翻的格子, 期望值)。"""
    state = tuple(state)
    options = [(c, _reveal_ev(state, c)) for c in range(9) if not state[c]]
    return max(options, key=lambda x: x[1])


def decide(state):
    """统一入口：已翻 <4 格返回 ('reveal', cell, ev)，否则 ('line', name, ev)。"""
    state = tuple(state)
    if sum(1 for v in state if v) < 4:
        c, ev = best_reveal(state)
        return ("reveal", c, ev)
    name, ev = best_line(state)
    return ("line", name, ev)


if __name__ == "__main__":
    import sys, time
    if len(sys.argv) > 1:          # 例: python solver.py 000050000
        st = tuple(int(ch) for ch in sys.argv[1])
        print(decide(st))
        sys.exit()
    t = time.time()
    overall = 0
    for pos in range(9):
        row = []
        for v in range(1, 10):
            s = [0] * 9
            s[pos] = v
            c, ev = best_reveal(s)
            row.append(f"{v}->翻{c}({ev:.0f})")
            overall += ev
        print(f"初始格{pos}: " + "  ".join(row))
    print(f"整体期望: {overall/81:.1f} 星砂/次   用时 {time.time()-t:.1f}s")
