# ArXiv Paper Processing

This project focuses on processing arXiv papers to extract relevant information and generate citation and performance networks.

## Steps to Generate Leaderboard

1. Convert PDFs to XML: Start by converting all the arXiv papers in PDF format into XML. Use the Grobid tool to convert the PDF files to XML format, ensuring the XML files have the necessary structure and tags for easy parsing.

2. Parse XML Files: Utilize XML parsing techniques to extract essential information from the generated XML files. You can use libraries like BeautifulSoup, which provide convenient methods for parsing XML and extracting data.

3. Generate Citation Network: Run the `AP_CN.ipynb` notebook to analyze and play wiht the parsed papers and generate a citation network. This network provides insights into the citations among the arXiv papers, enabling further analysis and visualization.

4. Generate Performance Network: Execute the `AP_PCN.ipynb` notebook to play and  generate the performance network. This network helps identify and analyze the performance of various arXiv papers based on predefined criteria.

Note: Make sure to adjust the scripts and configurations as necessary to suit your specific requirements and environment.

## Installation and Dependencies

To run this project, you will need the following dependencies:
- Python 3.x
- Grobid tool for PDF to XML conversion
- BeautifulSoup library for XML parsing
- Graph analysis library (e.g., `networkx` and `snap`)

Please refer to the respective documentation and installation guides for each dependency.

## Usage

1. Convert PDFs to XML:
   - Place the arXiv papers in PDF format in a designated folder.
   - Use the Grobid tool to convert the PDF files to XML format, ensuring the XML files have the necessary structure and tags for easy parsing.

2. Parse XML Files:
   - Modify the parsing script  to extract the required information from the XML files using the BeautifulSoup library.
   - Run the script to parse the XML files and store the extracted data in a structured format (e.g., CSV, JSON).

3. Generate Citation Network:
   - Ensure the parsed data is in a suitable format for the `AP_CN` notebook.
   - Run the `AP_CN` notebook, which will analyze the citation relationships among the arXiv papers and generate a citation network graph.

4. Generate Performance Network:
   - Prepare the necessary data based on the defined performance criteria.
   - Run the `AP_PCN` notebook, which will analyze the data and generate the performance network graph.

<!-- ## Contributing

Contributions to this project are welcome. Please follow the guidelines outlined in the CONTRIBUTING.md file.

## License

This project is licensed under the [MIT License](LICENSE). -->

## Contact

For any inquiries or suggestions, please contact the project authors:

- Shoaib Alam
  - Email: shoaib.alam@example.com

- Shruti Singh
  - Email: shruti.singh@example.com

- Mayank Singh
  - Email: mayank.singh@example.com

We appreciate your interest and contributions!
