import pandas as pd
import matplotlib.pyplot as plt

def plot_scores():
    # Assuming the JSON data is stored in 'data.json'
    df = pd.read_json('scores.json')

    # Calculate the mean for each player (column)
    average_scores = df.mean()

    # Calculate the percentage improvements
    percent_improvements = {}
    for player in average_scores.index:
        other_players = average_scores.drop(player)
        improvements = (average_scores[player] - other_players) / other_players * 100
        percent_improvements[player] = improvements.mean()

    # Plotting
    ax = average_scores.plot(kind='bar', color='skyblue', figsize=(8, 6))
    plt.title('Average Number of Games Won by Each Player')
    plt.xlabel('Player')
    plt.ylabel('Average Games Won')
    plt.xticks(rotation=0)

    # Annotate each bar with the numerical value and the average percentage improvement inside the bar
    for bar in ax.patches:
        height = bar.get_height()

        # Display the average score on the bar
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.5, f'{height:.2f}',
                ha='center', va='bottom')

        # Display the average percentage improvement inside the bar
        improvement_index = average_scores.index.tolist()[ax.patches.index(bar)]
        improvement = percent_improvements[improvement_index]
        ax.text(bar.get_x() + bar.get_width() / 2, height - 15, f'{improvement:.2f}%',
                ha='center', va='top', color='red', fontsize=9)

    plt.show()

if __name__ == "__main__":
    plot_scores()