## YAKINDU Merge Tool

YAKINDU Statechart Tools is an Eclipse-based editor where you can create state machines and generate code from it. 
Their  documentation is found [here](https://www.itemis.com/en/yakindu/state-machine/)

This python tool helps collaboration within YAKINDU Statechart Tools. It introduces the possibility of using different components and a template to generate one final statechart.
In the different components, you can choose which parts are migrated. 

The yakmerge tool is easily installed by running

```
pip install yakindu-merge-py
```

Afterwards you can invoke the following commando with the files that are in the example folder.

```
yakmerge -o ./example/final.ysc -t ./example/TrafficLightTemplate.ysc ./example/TrafficLightOn.ysc ./example/TrafficLightOff.ysc
```

Every component needs to have one composite state with the filename surrounded by underscores. 
TrafficLightOn.ysc has a composite state with \_TrafficLightOn\_ and TrafficLightOff.ysc -> \_TrafficLightOff\_. 
The template has two composite state. The template defines the interaction between the different components. 

The final.ysc is produced. It is also possible to overwrite the template when omitting the -o option. But be aware that this overwrite the template file. 

The definition is not migrated, each component needs to have a copy.