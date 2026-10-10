import random
from collections import Counter
import numpy as np
from game_env import HighLowEnv

class OptimalSolverAI:
    def __init__(self):
        pass

    def get_best_action(self, current_card, remaining_deck):
        """
        現在のカードと残りの山札から、期待値が最も高い行動(0 or 1)を算出する
        """
        curr_num, curr_suit = current_card
        total_remaining = len(remaining_deck)

        if total_remaining == 0:
            return 0

        # 行動タイプの判定
        if curr_num == 2 or curr_num == 14:
            action_type = 'COLOR'
        else:
            action_type = 'HIGH_LOW'

        if action_type == 'COLOR':
            # 赤と黒の残り枚数をカウント
            red_count = sum(1 for n, s in remaining_deck if s == 'R')
            black_count = total_remaining - red_count

            # 枚数が多い方の色を選択（0: 赤, 1: 黒）
            return 0 if red_count >= black_count else 1

        else: # HIGH_LOW
            # 2~14の各数字の残り枚数を集計
            counts = Counter([n for n, s in remaining_deck])

            high_win_cards = sum(counts[n] for n in range(curr_num + 1, 15))
            low_win_cards = sum(counts[n] for n in range(2, curr_num))
            same_cards = counts[curr_num]

            # 1. HIGHを選んだ場合の期待ペナルティ（失敗時に払うチップの平均）
            # HIGHで失敗＝curr_num未満のカードが出た場合
            low_cards_sum = sum(n * counts[n] for n in range(2, curr_num))
            penalty_if_high_fails = low_cards_sum / total_remaining if low_win_cards > 0 else 0

            # 2. LOWを選んだ場合の期待ペナルティ
            # LOWで失敗＝curr_numより大きいカードが出た場合
            high_cards_sum = sum(n * counts[n] for n in range(curr_num + 1, 15))
            penalty_if_low_fails = high_cards_sum / total_remaining if high_win_cards > 0 else 0

            # 期待値評価 (成功確率 * +1 - 失敗確率 * 期待ペナルティ)
            p_high_win = high_win_cards / total_remaining
            p_low_win = low_win_cards / total_remaining

            ev_high = (p_high_win * 1.0) - penalty_if_high_fails
            ev_low = (p_low_win * 1.0) - penalty_if_low_fails

            # 期待値が高い方を選択 (0: HIGH, 1: LOW)
            return 0 if ev_high >= ev_low else 1

# テスト実行（最適AI vs ランダムAI の 1000ゲーム対戦検証）
def evaluate_optimal_ai():
    env = HighLowEnv(num_players=2)
    solver = OptimalSolverAI()

    optimal_wins = 0
    random_wins = 0
    draws = 0

    games = 1000
    print(f"--- 最適戦略AI vs ランダムAI ({games}回対戦検証) ---")

    for g in range(games):
        obs = env.reset()
        done = False

        while not done:
            curr_p = env.current_player
            
            if curr_p == 0:
                # 最適戦略AI（山札の残りを完ぺきに把握して計算）
                action = solver.get_best_action(env.current_card, env.deck)
            else:
                # ランダムAI
                action = random.choice([0, 1])

            _, _, done, _ = env.step(action)

        active = [i for i in range(2) if env.lives[i] > 0]
        if len(active) == 1:
            if active[0] == 0:
                optimal_wins += 1
            else:
                random_wins += 1
        else:
            draws += 1

    print(f"【結果】")
    print(f"最適戦略AIの勝率: {optimal_wins / games * 100:.1f}% ({optimal_wins}勝)")
    print(f"ランダムAIの勝率  : {random_wins / games * 100:.1f}% ({random_wins}勝)")
    print(f"引き分け        : {draws / games * 100:.1f}% ({draws}回)")

if __name__ == "__main__":
    evaluate_optimal_ai()
