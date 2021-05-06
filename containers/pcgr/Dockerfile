FROM sigven/pcgr:0.9.1 

# Metadata
LABEL software="pcgr" \
      software.version="0.9.1" \
      about.home="https://github.com/sigven/pcgr" \
      about.summary="Personal Cancer Genome Reporter (PCGR) - variant interpretation for precision cancer medicine" \
      about.documentation="https://pcgr.readthedocs.io/en/latest/?badge=latest" \
      about.license="https://github.com/sigven/pcgr/blob/master/LICENSE"


RUN apt-get update \
  && apt-get install wget zip procps -y

# Install PCGR Python depency
RUN conda install toml

# Install PCGR source files
RUN wget https://github.com/sigven/pcgr/archive/refs/tags/v0.9.1.zip
RUN unzip v0.9.1.zip && rm v0.9.1.zip

ENV PATH /pcgr-0.9.1:$PATH
ENV PATH /pcgr-0.9.1/src:$PATH