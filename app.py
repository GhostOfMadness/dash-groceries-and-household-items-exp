# import pandas as pd
# import plotly.express as px
# from dash import Dash, dcc, html

# app = Dash(
#     __name__,
#     meta_tags=[
#         {'name': 'author', 'content': 'Daria Ovechkina'},
#     ],
#     title='Expenses Overview',
# )

# fig = px.scatter(
#     pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]}),
#     x='col1',
#     y='col2',
# )
# app.layout = html.Div(
#     html.Div('Personal expenses overview', className='card'),
# )

# if __name__ == '__main__':
#     app.run_server(debug=True)
