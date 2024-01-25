from __future__ import annotations
from typing import Optional, Iterable, Callable, Tuple
import math

class ScatterplotInfo:
    def __init__(self, x_vals: Iterable[float], y_vals: Iterable[float],
                 title: str, x_label: str, y_label: str):
        self.x_vals, self.y_vals, self.title = list(x_vals), list(y_vals), title
        self.x_label, self.y_label = x_label, y_label

    def invert(self) -> ScatterplotInfo:
        return ScatterplotInfo(self.y_vals, self.x_vals, self.title, self.y_label, self.x_label)
    
    def fit_to_polynomial(self, degree: int) -> str:
        import numpy as np
        poly_fit = np.polyfit(self.x_vals, self.y_vals, degree)
        poly_string = "y = "
        for i in range(degree+1):
            if i > 0:
                poly_string += ' + ' if poly_fit[i] >= 0 else ' - '
            poly_string += str(round(abs(poly_fit[i]), 6))
            if poly_string.endswith('.0'):
                poly_string = poly_string[:-2]
            exp = degree - i
            if exp >= 2:
                poly_string += f'x^{exp}'
            elif exp == 1:
                poly_string += 'x'
        return poly_string

def output_scatterplots(info_for_figs: Iterable[ScatterplotInfo]) -> None:
    import matplotlib.pyplot as plt
    import mplcursors # type: ignore
    for i, fig_info in enumerate(info_for_figs):
        f = plt.figure(i+1)
        plt.scatter(fig_info.x_vals, fig_info.y_vals, marker='o')
        mplcursors.cursor(hover=True)
        plt.title(fig_info.title)
        plt.xlabel(fig_info.x_label)
        plt.ylabel(fig_info.y_label)
        plt.grid(True)
        f.show()
    input("Enter any key to exit: ")

class QuadraticFunc:
    def __init__(self, a: float, b: float, c: float, 
                 req_for_x_vals: Optional[Callable[[float], bool]] = None,
                 req_for_y_vals: Optional[Callable[[float], bool]] = None):
        "Represents some function: y = ax^2 + bx + c"
        self.a, self.b, self.c = a, b, c
        self.req_for_x_vals, self.req_for_y_vals = req_for_x_vals, req_for_y_vals

    def y_val(self, x_val: float) -> float:
        if self.req_for_x_vals:
            assert self.req_for_x_vals(x_val)
        return self.a*x_val**2 + self.b*x_val + self.c
    
    def x_vals(self, y_val: float) -> Tuple[float, float]:
        """Returns the roots of the equation when substituting `y_val` for y."""
        # Need to make a quadratic equation. Do this by substituting y_val for y,
        # then subtracting it from both sides. This just makes c become self.c - y.
        if self.req_for_y_vals:
            assert self.req_for_y_vals(y_val)
        a, b, c = self.a, self.b, self.c - y_val
        sqrt_exp = math.sqrt(b**2 - 4*a*c)
        return ((-b+sqrt_exp)/(2*a), (-b-sqrt_exp)/(2*a))