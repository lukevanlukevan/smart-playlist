import json
import plotly.graph_objects as go
import pandas as pd


def lerp(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)



def do_plot():

    with open("playlist_info.json", "r") as f:
        playlist = json.load(f)
    use = {
        "danceability": {
            "range": [0, 1],
        },
        "energy": {
            "range": [0, 1],
        },
        "key": {
            "range": [-1, 11],
        },
        "loudness": {
            "range": [-60, 0],
        },
        "mode": {
            "range": [0, 1],
        },
        "speechiness": {
            "range": [0, 1],
            "hide": True,
        },
        "acousticness": {
            "range": [0, 1],
        },
        "instrumentalness": {
            "range": [0, 1],
        },
        "liveness": {
            "range": [0, 1],
        },
        "valence": {
            "range": [0, 1],
        },
        "tempo": {
            "range": [40, 200],
            "hide": False,
        }

    }

    data = [label for label in playlist[0]['features'].keys() if label in use]

    fig = go.Figure()
    for i, label in enumerate(playlist):
        values = [lerp(label['features'][track], use[track]['range'][0], use[track]['range'][1]) for track in data if not use[track].get('hide', False)]
        data = [track for track in data if not use[track].get('hide', False)]

        df = pd.DataFrame(dict(
            r=values,
            theta=data
        ))

        fig.add_trace(
            go.Scatterpolar(
                r=df['r'],
                theta=df['theta'],
                # fill="toself",  # No fill
                fill=None,
                name=f"{label['name']} ({label['artist']})",
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True
    )

    fig.show()
