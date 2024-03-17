import matplotlib.pyplot as plt

def get_data_from_ratings(ratings):
  return list(map(lambda x: x["mu"], ratings))

def clear():
  plt.close()

def graph_tournament(tournament_ratings, tournament_name): #player_ratings['by_event'][event]
  # max_num_games = max(map(len, player_ratings.values()))
  for player in tournament_ratings:
    plt.plot(get_data_from_ratings(tournament_ratings[player]), label=player)
  
  plt.legend()
  plt.savefig(f"images/{tournament_name}.png", bbox_inches='tight')

def graph_player(event_ratings, player_name, granularity):
  consolidated_ratings = [{"mu": 1200}] # initialize starting point. technically should also be part of the data somewhere
  for event in event_ratings:
    if player_name in event_ratings[event]:
      if granularity == "event":
        consolidated_ratings.append(event_ratings[event][player_name][-1])
      elif granularity == "game":
        consolidated_ratings.extend(event_ratings[event][player_name])

  plt.plot(get_data_from_ratings(consolidated_ratings), label=player_name)

def graph_and_save_player(event_ratings, player_name, granularity):
  graph_player(event_ratings, player_name, granularity)
  plt.legend()
  plt.savefig(f"images/{player_name}_by_{granularity}.png", bbox_inches='tight')

def graph_players(event_ratings, players, granularity):
  for player in players:
    graph_player(event_ratings, player, granularity)

  plt.legend()
  plt.savefig(f"images/player_group.png", bbox_inches='tight')
