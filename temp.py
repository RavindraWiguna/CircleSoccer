total_pop = 50
total_match_per_pair=5

score_per_goal=30
score_win = 100
score_lose=-100
rate_goal = 0.5
min_full_score = score_win+score_per_goal+1
max_bad_score = score_lose - 1

total_pair = total_pop*(total_pop-1)/2
total_game = total_pair*total_match_per_pair

fitness = total_game*rate_goal*min_full_score + (1-rate_goal)*max_bad_score*total_game
print(fitness)