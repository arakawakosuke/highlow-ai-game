import random
from collections import Counter

class OptimalSolverAIV2:
    def __init__(self):
        pass

    def get_best_action(self, current_card, deck, my_lives, opp_lives, pot):
        """
        4要素（自分の残機・相手の残機・ポット額・カードカウント）を考慮した最強の意思決定
        
        0: HIGH / RED
        1: LOW / BLACK
        """
        curr_num, curr_suit = current_card
        total_remaining = len(deck)

        if total_remaining == 0:
            return 0, "山札なし"

        # 1. 2 または A(14) の場合は色予想
        if curr_num == 2 or curr_num == 14:
            red_count = sum(1 for n, s in deck if s == 'R')
            black_count = total_remaining - red_count
            chosen = 0 if red_count >= black_count else 1
            reason = f"色カウント (赤:{red_count}枚 / 黒:{black_count}枚)"
            return chosen, reason

        # 2. HIGH / LOW の確率・平均ペナルティ算出（カードカウント）
        counts = Counter([n for n, s in deck])

        high_win_cards = sum(counts[n] for n in range(curr_num + 1, 15))
        low_win_cards = sum(counts[n] for n in range(2, curr_num))

        p_high = high_win_cards / total_remaining
        p_low = low_win_cards / total_remaining

        # 失敗時の平均ペナルティ額
        low_cards_sum = sum(n * counts[n] for n in range(2, curr_num))
        penalty_if_high_fails = low_cards_sum / total_remaining if low_win_cards > 0 else 0

        high_cards_sum = sum(n * counts[n] for n in range(curr_num + 1, 15))
        penalty_if_low_fails = high_cards_sum / total_remaining if high_win_cards > 0 else 0

        # =========================================================
        # 3. 4要素を反映した総合価値評価関数 (Value Function) の設計
        # =========================================================

        # A. 残機リスク係数 (Life Risk Factor)
        # 自分の残機が1の時は脱落（敗北）のリスクが極めて高いため、成功確率重視に重み付け
        if my_lives == 1:
            risk_weight = 2.5  # ペナルティを大袈裟に評価し、純粋な生き残り（高勝率）を最優先
        elif my_lives == 2:
            risk_weight = 1.2
        else:
            risk_weight = 0.8  # 残機3の時は多少のリスクを取れる

        # B. ポットインセンティブ (Pot Incentive)
        # ポットにチップが溜まっているほど、正解してゲームを生き延びた時の見返りが大きい
        pot_bonus = 1.0 + (pot * 0.15)

        # C. 相手プレッシャー (Opponent Pressure)
        # 相手の残機が1の時、安全に攻めてターンを渡すことで相手の自爆を狙う戦略的価値
        opp_safety_bonus = 0.3 if opp_lives == 1 else 0.0

        # 総合評価値 (EV_v2) の計算
        # EV = (成功確率 * (基本リワード + ポットボーナス + プレッシャー)) - (失敗確率 * 平均ペナルティ * 残機リスク)
        ev_high = (p_high * (1.0 + pot_bonus + opp_safety_bonus)) - ((1.0 - p_high) * penalty_if_high_fails * risk_weight)
        ev_low = (p_low * (1.0 + pot_bonus + opp_safety_bonus)) - ((1.0 - p_low) * penalty_if_low_fails * risk_weight)

        chosen = 0 if ev_high >= ev_low else 1

        reason = (f"【4要素評価】(自残機:{my_lives}, 敵残機:{opp_lives}, Pot:{pot}) "
                  f"HIGH(勝率{p_high*100:.1f}%, 評価値:{ev_high:.2f}) vs "
                  f"LOW(勝率{p_low*100:.1f}%, 評価値:{ev_low:.2f}) -> {'HIGH' if chosen==0 else 'LOW'}")

        return chosen, reason


# スクリプト直接実行時の簡易テスト
if __name__ == "__main__":
    solver = OptimalSolverAIV2()
    
    # 疑似山札（51枚想定）
    dummy_deck = [(n, s) for n in range(2, 15) for s in ['R', 'R', 'B', 'B']]
    dummy_deck.pop()

    card = (8, 'R') # 場が 8

    # シーン1: 通常時（残機3, ポット0）
    act1, r1 = solver.get_best_action(card, dummy_deck, my_lives=3, opp_lives=3, pot=0)
    print("場面1 (通常時):", r1)

    # シーン2: ポット大量・自分の残機1（背水の陣）
    act2, r2 = solver.get_best_action(card, dummy_deck, my_lives=1, opp_lives=3, pot=25)
    print("場面2 (背水・高ポット):", r2)
