import os
from flask import Flask, render_template, jsonify, request
from collections import Counter
from game_env import HighLowEnv
from solver_v2 import OptimalSolverAIV2

app = Flask(__name__)
env = HighLowEnv(num_players=2)
solver = OptimalSolverAIV2()

# 通算成績を保持するグローバル変数
stats = {
    'total_games': 0, 'human_wins': 0, 'ai_wins': 0, 'draws': 0,
    'human_chips': 0, 'ai_chips': 0
}
game_recorded = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/reset', methods=['POST'])
def reset():
    global game_recorded
    game_recorded = False
    env.reset()
    resp = build_response("ゲーム開始！最初の場のカードに対してアクションを選択してください。")
    resp['is_done'] = False
    resp['is_ai_turn'] = False
    return jsonify(resp)

@app.route('/api/reset_stats', methods=['POST'])
def reset_stats():
    global stats, game_recorded
    stats = {'total_games': 0, 'human_wins': 0, 'ai_wins': 0, 'draws': 0, 'human_chips': 0, 'ai_chips': 0}
    game_recorded = False
    env.reset()
    resp = build_response("成績をリセットしました")
    resp['is_done'] = False
    resp['is_ai_turn'] = False
    return jsonify(resp)

def check_and_record_game_over(done):
    """ゲーム終了判定と成績の記録を安全に行うヘルパー関数"""
    global game_recorded
    
    active_players = [i for i in range(2) if env.lives[i] > 0]
    is_done = done or len(active_players) <= 1 or len(env.deck) == 0

    winner = None
    if is_done:
        if env.lives[0] > env.lives[1]:
            winner = "Player (あなた)"
        elif env.lives[1] > env.lives[0]:
            winner = "AI"
        else:
            winner = "引き分け"

        # まだこのゲームの成績が記録されていなければ、1回だけ厳密に加算する
        if not game_recorded:
            stats['total_games'] += 1
            if env.lives[0] > env.lives[1]:
                stats['human_wins'] += 1
                stats['human_chips'] += env.pot
            elif env.lives[1] > env.lives[0]:
                stats['ai_wins'] += 1
                stats['ai_chips'] += env.pot
            else:
                stats['draws'] += 1
            game_recorded = True

    return is_done, winner

@app.route('/api/step', methods=['POST'])
def step():
    data = request.get_json()
    action = data.get('action')

    info, done = env.step(action)
    is_done, winner = check_and_record_game_over(done)

    resp = build_response(info)
    resp['is_done'] = is_done
    resp['winner'] = winner
    resp['is_ai_turn'] = (not is_done and env.current_player == 1)
    return jsonify(resp)

@app.route('/api/ai_step', methods=['POST'])
def ai_step():
    if env.is_color_phase:
        red_count = sum(1 for n, s in env.deck if s == 'R')
        black_count = len(env.deck) - red_count
        ai_action = 0 if red_count >= black_count else 1
        ai_action_str = "RED (赤)" if ai_action == 0 else "BLACK (黒)"
    else:
        ai_action, _ = solver.get_best_action(
            current_card=env.current_card,
            deck=env.deck,
            my_lives=env.lives[1],
            opp_lives=env.lives[0],
            pot=env.pot
        )
        ai_action_str = "HIGH" if ai_action == 0 else "LOW"

    info, done = env.step(ai_action)
    is_done, winner = check_and_record_game_over(done)

    resp = build_response(f"AIの選択[{ai_action_str}]: {info}")
    resp['is_done'] = is_done
    resp['winner'] = winner
    resp['is_ai_turn'] = (not is_done and env.current_player == 1)
    return jsonify(resp)

def build_response(last_info):
    st = env.get_state()
    deck_counts = Counter([num for num, suit in env.deck])
    counts_dict = {num: deck_counts[num] for num in range(2, 15)}
    red_count = sum(1 for n, s in env.deck if s == 'R')
    black_count = len(env.deck) - red_count

    win_rate = (stats['human_wins'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0.0

    return {
        'card_num': st['card_num'],
        'card_suit': st['card_suit'],
        'action_type': st['action_type'],
        'remaining_deck': st['remaining_deck'],
        'pot': st['pot'],
        'lives_human': st['lives_human'],
        'lives_ai': st['lives_ai'],
        'current_player': st['current_player'],
        'is_color_phase': st['is_color_phase'],
        'counts': counts_dict,
        'red_count': red_count,
        'black_count': black_count,
        'last_info': last_info,
        'stats': {
            'total_games': stats['total_games'],
            'human_wins': stats['human_wins'],
            'ai_wins': stats['ai_wins'],
            'draws': stats['draws'],
            'win_rate': round(win_rate, 1),
            'human_chips': stats['human_chips'],
            'ai_chips': stats['ai_chips']
        }
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
