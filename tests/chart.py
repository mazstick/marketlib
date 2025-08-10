import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.collections
import matplotlib.animation as animation
import mplfinance as mpf

# بارگذاری داده‌ها
df = pd.read_csv("E:/Work/Test/btc15m.csv", parse_dates=["Datetime"], index_col="Datetime")

# مرحله ۱: ساخت کامل با mplfinance
fig_mpf, axlist = mpf.plot(
    df[:400],  # فقط ۳۰ کندل اول
    type='candle',
    style='charles',
    returnfig=True,
    figscale=1.5,
    axisoff=False,
    volume=False,
)


# استخراج کندل‌ها از PolyCollection
ax_mpf = axlist[0]
print(ax_mpf.get_children()[8])
poly = ax_mpf.get_children()[1]  # مجموعه‌ی کندل‌ها
paths = poly.get_paths()
colors = poly.get_facecolors()
verts = [p.vertices for p in paths]

lines = ax_mpf.get_children()[0]  # مجموعه‌ی کندل‌ها



# مرحله ۲: ساخت پنجره‌ی جدید برای انیمیشن
fig_anim, ax_anim = plt.subplots(figsize=(10, 6))
ax_anim.set_xlim(ax_mpf.get_xlim())
ax_anim.set_ylim(ax_mpf.get_ylim())

def animate(i):
    ax_anim.get_children().clear()
    poly_new = matplotlib.collections.PolyCollection(verts[:i+1], facecolors=colors[:i+1])
    ax_anim.add_collection(poly_new)
    return poly_new,

ani = animation.FuncAnimation(fig_anim, animate, frames=len(verts), interval=10, blit=False)
plt.show()
