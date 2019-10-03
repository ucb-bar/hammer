Hammer Actions
===================================

As described in the Hammer Overview, Hammer has a set of actions including synthesis, place-and-route, DRC, LVS, simulation, and more. Hammer automatically takes the outputs of each action and feeds them to subsequent actions where they are needed. The sets up a sort of dependency graph of the actions in which the nodes are actions and the edges are steps that convert the outputs of the source action to the inputs of the sink action.  This graph is illustrated below and is meant to visualize
the different Hammer steps and how they interact with each other.

INSERT GRAPHIC HERE

All of the Hammer actions and their associated key inputs can be found in ``hammer/src/hammer-vlsi/defaults.yml`` and are documented in detail in each action's documentation.

TODO: talk about intermediate steps

