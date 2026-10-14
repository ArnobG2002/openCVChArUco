import numpy as np
import matplotlib.pyplot as plt
import json


with open('JsonStructure.json', 'r') as openfile:
        # Reading from json file
        json_object1 = json.load(openfile)
        cameraConfig1=json_object1['cameraConfig']
cameraConfig2=[i.replace('Default\\', '') for i in cameraConfig1]
# Plot
fig, ax = plt.subplots(constrained_layout=True)
cmap = plt.get_cmap('viridis')
colors = cmap(np.linspace(0, 1, len(cameraConfig2)))
for i in cameraConfig2:
    with open(i, 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)
    c=np.random.rand(3,)
    ax.scatter(json_object['Data']['Eye'][0], json_object['Data']['Eye'][2], label=json_object['Data']['Name'], color=c)
    # Draw camera direction arrow
    ax.quiver(json_object['Data']['Eye'][0], json_object['Data']['Eye'][2],
          -json_object['Data']['Eye'][0]+json_object['Data']['Lookat'][0], -json_object['Data']['Eye'][2]+json_object['Data']['Lookat'][2],
          angles='xy', scale_units='xy', scale=0.01,
          color=c)
ax.plot([-341.4/16, (15/16)*341.4], [0,0], c='blue', label='FoLD')
#ax.plot([(15/16)*341.4 - 700*np.tan(np.pi/6), (15/16)*341.4], [700,0], c='grey')
#ax.plot([-341.4/16 + 700*np.tan(np.pi/6), -341.4/16], [700,0], c='grey')
ax.fill_betweenx([800,0], [(15/16)*341.4 - 800*np.tan(np.pi/6), (15/16)*341.4], [(15/16)*341.4 + 800*np.tan(np.pi/6), (15/16)*341.4], color='grey', alpha=0.1)
ax.fill_betweenx([800,0], [-341.4/16 + 800*np.tan(np.pi/6), -341.4/16], [-341.4/16 - 800*np.tan(np.pi/6), -341.4/16], color='grey', alpha=0.1)

ax.set_xlabel('X (mm)')
ax.set_ylabel('Z (mm)')
ax.set_title('Bottom-Up View (XZ Plane)')
ax.legend(bbox_to_anchor=(0, -0.4, 1, 1), loc='lower left',
                      ncols=6, mode="expand", borderaxespad=0.)
ax.grid(True)
plt.savefig('all.png', dpi=100)
#plt.show()
