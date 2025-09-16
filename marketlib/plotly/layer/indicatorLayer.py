class IndicatorPlotlyLayer:

    def __init__(self):
        self.panel_hight = 0.3
        self.colors = ["red", "blue"]
        self.width = [1, 1.9]
        self.name = "unknown"
        self.panel = [1, 1, 1]
        self.opacity = [1, 0.5]
        self.hovertemplate = "Value: %{y:.2f}<br>Time: %{x}"
