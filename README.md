# IMC_Prosperity

Repository containing the code from [IMC Prosperity](https://prosperity.imc.com/)'s challenge. 

## :scroll: Rules

The purpose of this competition is to utilize various techniques of data analysis and quantitative finance to trade commodities with diverse behaviors.

The competition comprises five rounds, each involving the introduction of new commodities exhibiting distinct behaviors.

### Round 1

    Participants have worked with two assets, namely **PEARLS**, whose price remains relatively constant over time at a value of 10k seashells, and **BANANAS**, an asset whose price is highly volatile, fluctuating frequently.

### Round 2

    Participants have been provided with data on **COCONUTS** and **PINA_COLADAS**. Although the price of COCONUTS and PINA_COLADAS are related, as coconuts are required for the production of pina coladas, the converse is not true.

### Round 3

    Two additional assets were introduced, **BERRIES** and **DIVING_GEAR**. The price of BERRIES is seasonal, while that of DIVING_GEAR is influenced by **DOLPHIN_SIGHTINGS**, another data set provided by IMC. The latter may serve as a feature for predicting the price of DIVING_GEAR.

### Round 4

    Participants have worked with four assets, namely **PICNIC_BASKET**, **UKULELE**, **DIP**, and **BAGUETTE**. We have been informed that one PICNIC_BASKET consists of one UKULELE, two BAGUETTEs, and four DIPs. However, the price of PICNIC_BASKET is not equivalent to the sum of the prices of its individual components.

### Round 5

    During this round, participants were granted access to IMC trader bots and were given the opportunity to replicate, or take profit from the strategy of the most experienced bots.

## :computer: Our strategies

### Round 1

Regarding PEARLS, we will put bid orders at 10k - 1 and ask orders at 10k + 1, since the price is consistently stable at 10k.

For BANANAS we put bid orders at EMA - 1 and ask orders at EMA + 1, where EMA is the exponential moving average:

$$
    EMA_{t} = \alpha P_{t} + (1-\alpha) EMA_{t-1}
$$

Where $t$ is the current time, $\alpha$ is an hyperparameter and $P_{t}$ is the current mid price.

### Round 2

In this round, we created a pair trading strategy between COCONUT and PINA_COLADAS. Then we traded on the spread:

$$
    Spread = P_{t, \ PINA \ COLADAS} - P_{t, \ COCONUTS}
$$

* When the z-score of the spread is higher than 1.5, we shorted the spread (*i.e* we buy COCONUTS and sell PINA_COLADAS)

* When the z-score of the spread is lower than -1.5, we bought the spread (*i.e.*, we buy PINA_COLADAS and sell coconuts)

### Round 3

For BERRIES, we verified that the price starts rising at $ t_{long} = 2e5 $ and after $ t_{short} = 5e5 $, it starts falling. Then, we buy at $ t_{long} $ and sell at $ t_{short} $

For DIVING_GEARs we verified that big jumps in the derivative of DOLPHIN_SIGHTINS implied in future jumps in DIVING_GEARs prices.