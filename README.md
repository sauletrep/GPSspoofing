# Assignment 1
## GPS Spoofing Detection with Parallel Computing

Goal:
Analyze vessel tracking data from AIS records using parallel processing techniques to detect GPS spoofing events. Students will focus on efficient data handling, transformation, and performance evaluation using Python's parallel computing capabilities.

## Dataset: 25.08.2024
http://web.ais.dk/aisdata/  

## Submission and Presentation
* Deadline: All tasks (1-4) must be completed and submitted by the specified end date and time.
* Presentation Format: Up to 5 slides covering solutions to tasks 1-4.
* Requirement: Students must submit their code to a specified code repository (GitHub, GitLab).

### Evaluation Criteria

* Category -> Description
* Code Quality -> Clarity, efficiency, and correctness of the implementation.
* GPS Spoofing Detection ->	Accuracy and effectiveness in detecting spoofing events.
* Performance Analysis -> Depth of parallel processing efficiency evaluation, speedup calculations, and visualization of results.
* Use of Vilnius University HPC (+1 Point)	-> Proper execution and documentation of results on the HPC system.
* Presentation ->	Clarity and conciseness in explaining the solution.


# 1. Parallel Splitting of the Task

### Parallel Computing Techniques
One of the most widely used classifications of parallel computing techniques is Flynn’s Taxonomy. This taxonomy defines four main types of computing architectures:

Single Instruction stream, Single Data stream (SISD): This refers to traditional serial computing, where a single processor executes a single stream of instructions on a single set of data. Since there is no parallel execution, SISD is not considered a parallel computing technique. 

Single Instruction stream, Multiple Data stream (SIMD): This is a parallel computing technique where multiple processing units execute the same instruction on different data elements simultaneously. 

Multiple Instruction stream, Single Data stream (MISD): This is an uncommon type of parallel computing where a single stream of data is processed by multiple processors, each executing different instructions.

Multiple Instruction stream, Multiple Data stream (MIMD): This is the most common form of parallel computing. In MIMD, multiple processors execute different instructions on different data streams, allowing for a high degree of flexibility and scalability.

To efficiently process the data for this task, I will implement data parallelism using my 8 available processors. I will achieve this by dividing the dataset into discrete chunks, with each chunk being processed independently by a separate processor. The same GPS spoofing detection function will be applied to each chunk in parallel. However, the function may not process every data chunk identically. Depending on the specific characteristics of each chunk, additional steps might be required. For example, vessels navigating through high-traffic waters may require additional considerations when detecting GPS spoofing. While all processes execute the same function, the sequence of operations performed might differ based on the data characteristics.

This aligns with the MIMD parallel computing model because each processor operates independently, running its own instance of the GPS spoofing detection function on a separate chunk of data, meaning multiple data streams are processed simultaneously. By applying MIMD parallelism, I expect the GPS spoofing detection task to be completed faster than it would with a single processor (serial execution). However, the actual performance improvement will be evaluated later in Task 4.

### Workload balancing
I will be dividing the dataset into discrete chunks, where each chunk will consist of all the datapoints of a single vessle. This makes the GPS spoofing easier whilst creating an uneven distribution of computational effort among the processors. Some vessels have many more data points than others, and some vessles requirer additional computations and analysis. This can cause load imbalance, where some processes finish early while others keep running, reducing overall efficiency. 

By using map_unordered() rather than the basic map() for multiprocessing the processors that finish early get assigned new vessels dynamically, meaning that they immediately get a new chunk and do not have to wait for all the processes to finish. map() assigns equal-sized chunks to each worker before execution, meaning that the slower tasks would delay the overall computation. It is not usefull when the function being applied is to fast. In these cases the parallelism overhead outweighs the benefits. This is the case whilst I am setting up my program as well as using a smaller sample data. So untill I use the full data and the function being applied sucsesfully detects GPS spoofing I will continue to use map() but include chunksize=4. By default map() distributes one task at a time to each worker, so by setting a chunksize parameter I ensure that each worker gets a more balanced batch of tasks rather than assigning them one-by-one.

### Strategized division of AIS data processing into parallelizable sub-tasks.

#### Strategy:
*   Load the data (and load sample data (nrows = 100000) to use whilst working to create a better workflow)
*   Split the data into smaller chunks that can be processed in parallel.
  *  For GPS spooing detection the chunks will contain only the data from a single vessel. 
*   Use multiprocessing to process each chunk in parallel.
  *   Each task will be conected to the same function, but will be processed in parallel.
*   Combine results from each chunk after procesing.

# 2. Implementation of Parallel Processing
Objective: Develop Python code to process the AIS data in parallel for efficient computation.

Guidance: Utilize Python libraries for parallel processing.

Python code that processes th AIS data in parallel for efficient computation is in the file "AISParallelProcessing.py". THe function detect_gps_spoofing(vessel_data) will have to be modified for real GPS spoofing detection. In this function I have simply sat a constant limit for the change in latitude, longitude and speed between two timestamps for each vessle, not even taking into account the time between timestamps. This limit is the same for all vessels and has been chosen by simply reducing the number of possible spoofing cases detected. 

# 3. GPS Spoofing Detection
GPS spoofing is a technique in which someone deliberately manipulates GPS signals, causing receivers to display false location or time data. This can have serious consequences for maritime navigation and security.

## A. Identifying Location Anomalies:

Detect sudden, unrealistic location jumps that deviate significantly from expected vessel movement patterns.
## B. Analyzing Speed and Course Consistency:

Identify vessels with inconsistent speed changes or impossible travel distances within a short time.
## C. Comparing Neighboring Vessel Data:

Check if multiple vessels in the same region report conflicting GPS positions.

The implementation of Parallel Processing is in the file "SpoofingDetection.py" 

# 4. Evaluating Parallel Processing Efficiency
Objective: Measure and evaluate the performance efficiency of parallelized processing techniques.

Guidance:

*   Compare execution time between sequential and parallel implementations.
*   Use speedup analysis: Speedup=Time (sequential)Time (parallel)\text{Speedup} = \frac{\text{Time (sequential)}}{\text{Time (parallel)}}Speedup=Time (parallel)Time (sequential)
*   Analyze CPU and memory usage across different numbers of parallel workers.
*   Test different numbers of CPUs and chunk sizes and compare their impact on execution time.
*   Visualize results in a graph showing performance improvements across configurations.
*   Bonus (+1 point): Students who execute their code on the Vilnius University HPC system and document their experience will receive an additional +1 grade to their task score.



# 5. Presentation of the Solution
Objective: Effectively present the solution to the GPS spoofing detection task.

Guidance: Clearly explain the implemented techniques, performance improvements, and findings in a structured manner.
