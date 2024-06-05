#!/usr/bin/python3
"""Non overlapping Legends."""
import cv2
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


W_INCHES = 3

y0 = 0.3
x0 = 0.8
w0 = 2

def draw(scale: float):
    side = int(1000*scale)
    img = cv2.hconcat((np.zeros((side, side)), np.ones((side, side))))

    h, w = img.shape
    fig = plt.gcf()
    fig.set_size_inches(W_INCHES, h * W_INCHES/w)
    fig.set_dpi(w/W_INCHES)
    fig.tight_layout(pad=0)
    plt.axis('off')

    plt.imshow(img)
    plt.gca().autoscale(False)

    w1 = w
    x1 = (x0+0.5)*w1/w0 - 0.5

    h1 = h
    y1 =  (y0+0.5)*h1/w0 - 0.5

    plt.plot([x1, x1], [-0.5, h1-0.5])
    plt.text(x1, y1, f"Hello {scale:.2f}", ha='center', va='center')
    plt.savefig(f"data/{scale:.2f}.svg")

for scale in [0.1, 0.5, 1.0, 3.0, 10]:
    plt.figure()
    draw(scale)

# plt.show()

# plt.axis('off')
# plt.gcf().tight_layout(pad=0)
# plt.imshow(np.array([[0,1], [2,3]]))
# plt.plot([0,0,1,1,0], [0,1,1,0,0])
# plt.savefig("data/test.svg")