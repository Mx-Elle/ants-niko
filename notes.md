of all moves that a bot can make...

# grouped goal instructions
- winner used this
- for attacking or defending we want our ants to consolidate
- for food we want our ants to spread out
## get food
- assign some bots the task of seeking and getting food
- or maybe have ants that happen to be close get food
## attack
- stage ants while numbers increase before going to attack
- attack as large mass to not lose numbers
## defend
- create blockades around our hills
    - potentially have \# of ants protecting each hill as time goes on
    - either as one large mass around hill or expand a ring outward near entry points
- create barriers between large masses of enemy ants and strategic points
    - strategic points may be regions with a lot of food access or navigationally significant points
---

# theories
- create blocks to make it so that enemy ants have to go through our ants to get to our hills
- choke points will probably be important
- blocking choke points will require less ants than protecting open space
- the larger of a ring we have, the more safe and easily accesible food we will have

---
# implementation
## food grabber
food grabber v1 got stuck a lot\
most ants ended with random move\
sometimes ants were able to grab large mass of food if close enough to capture one square\
new implentation:
- get all food locations
- get all ant locations
- find closest ants to each food
    - for each ant iterate through foods to get nearest food and then iterate through that
    - *or* for each food iterate through ants to get nearest ant
    - both ideas require iteration through both food and ants... is there a better way?
- assign directions based off closest ant to each food
- once all food are assigned an ant, make the ants others explore
    - how am i going to create an exploring type ant?
    - does the walls array allow me to infer the dimensions of the map?
    - if i can get a sense of the map from the walls array, i should be able think of an exploring technique
\
\
might dijkstra map can be used for ant to food or food to ant...
**but** it might be more beneficial to have attacking or defending ants
travel towards their goal using a bellman-ford\
this would allow the food cells to have a very negative weight and influence
ants to pick up food on their way to a goal
