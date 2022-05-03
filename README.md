# YouTube Recommendation Political Content Silo Analysis

## Table of Contents
* [Introduction](#introduction)
* [Repository Organization](*repository-organization)
* [Data Collection](*data-collection)
* [Findings](*findings)

## Introduction
Welcome to the repo containing the work for both my individual research project for the Comp 396 course and its extension which will appear as "Chapter 4: Analysis of the impact of algorithms in siloing users: special focus on YouTube" of the upcoming book "AI & Society: Tensions and Opportunities" CRC Press Taylor & Francis Group co-authored by myself (Mika Desblancs) and Joseph Vybihal, Faculty Lecturer at McGill University ([personal website](https://www.cs.mcgill.ca/~jvybihal/index.php)).

In the chapter, we present a software probing method to examine the behaviour of a recommendation system and present how our method can be used to analyze the YouTube recommendation system. We describe three ways of traversing the recommendation expansion and using a set of novel metrics we measure the level of siloing over the course of the different recommendation expansion traversals. We present our results and find that political siloing is present in YouTube, however the recommendation system is sensitive to selection change (intentional attempts to watch opposing political content cause quick changes in the videos recommended).

## Repository Organization
For my Comp 396 project (Undergraduate Research Project Course): 
- the Final Report can be found in the "\Comp 396 Final Report.[pdf/docx]"([here](https://github.com/mika-jpd/YouTube_Radicalization_Recommendations/blob/master/Comp%20396%20Research%20Project/Comp%20396%20Final%20Report.pdf)),
- the Jupyter notebook with data used in the report can be found at "Comp 396 Research Project\Tree Analysys of YouTube Scraper.ipynb" ([here](https://github.com/mika-jpd/YouTube_Radicalization_Recommendations/blob/master/Comp%20396%20Research%20Project/Tree%20Analysys%20of%20YouTube%20Scraper.ipynb))
- the webscraper code used can be found at "\Comp 396 Research Project\YouTubeScraper.py" ([here](https://github.com/mika-jpd/YouTube_Radicalization_Recommendations/blob/master/Comp%20396%20Research%20Project/YouTubeScraper.py))
- the related YouTube webscrape data in "\Comp 396 Research Project\Project_data\" ([here](https://github.com/mika-jpd/YouTube_Radicalization_Recommendations/tree/master/Comp%20396%20Research%20Project/Project_data))
    - the first section called "Tree_Results (Left-Wing)" contains the data for webscrapes whose root video is a left-wing video
    - the second section called "Tree_Results (Right-Wing)" contains the data for webscrapes whose root video is a right-wing video

For the chapter data, all the relevant data and graphs are in "\YouTube Content Silos Research":
- the notebook with relevant analysis can be found in "YouTube Content Silos\Analysis of all experiments.ipynb"
- the data for the different scrapes can be found in "YouTube Content Silos\[Depth, Breadth, Survey]" folders

(*Note: As the Chapter content is propery of CRC Press Taylor & Francis Group, I am not able to include it in the repository. I will update the repo with a link for purchase once it is available for purchase.*)

## Data Collection
1. We first start by logging in to one of the accounts we created for this purpose
2. We then delete the user history to get a fresh homepage and recommended videos influenced only by the current user history
3. We travers the recommendation space in three different ways to mimmick three different traversals.


    i. Breadth-First:
    We begin by selecting a YouTube video from a curated list, then we explore the recommendation space in bread-first order with 3 leaves and a depth of 4. We pick the first three videos (regardless of their content), save their meta-data, and then proceeed to watch each of their recommended videos. The script takes a screenshot of the webpage after all videos at each *depth level* have been watched. 
    
    
    ii. Depth-First:
    
    We begin by selecting a YouTube video from a curated list, then we explore the recommendation space in depth-first order. We will watch the first 5 recommended videos of the root video and then only the first video for the subsequent recommended videos for a tree depth of 6. We call going down the recommended space of a recommended video of the root video a dive. After each dive we take a screenshot of the homepage videos.
    
    
    iii. Common-cycle procedure
    
    The algorithm will start by determining the user’s intentby using the following rule: 
        * 80% of the time it will choose to start with an initial left-/right-wing seed from the curated list of videos to generate the root recommendations of interest, based on its initial bias.
        * 10 % of the time itwill choose a video from the first 25 videos automatically presented to it when it first logged in (called the homepage-videos).
        * 10% of the time it will scan the homepage-videos for an opposing point of view, choosing a random homepage video if no partisan video is found. The algorithm then performs a depth-first search of the recommendation space guided by the user’s intent for a ply depth of 2. 

This will be repeated 6 times

## Findings
