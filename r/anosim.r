# Runs vegan function ANOSIM on QIIME distance file.
# usage:
# R --slave --args -d unifrac.txt -m Fasting_Map.txt -c Treatment -o anosim --source_dir $QIIME_HOME/qiime/support_files/R/ < anosim.r
# 
# print help string:
# R --slave --args -h --source_dir $QIIME_HOME/qiime/support_files/R/ < anosim.r
#
# Requires command-line param --source_dir pointing to QIIME R source dir
args <- commandArgs(trailingOnly=TRUE)
if(!is.element('--source_dir', args)){
    stop("\n\nPlease use '--source_dir' to specify the R source code directory.\n\n")
}
sourcedir <- args[which(args == '--source_dir') + 1]

# load libraries and source files
source(sprintf('%s/loaddata.r',sourcedir))
source(sprintf('%s/util.r',sourcedir))
load.library('optparse')
load.library('vegan')

# make option list and parse command line
option_list <- list(
    make_option(c("-d", "--distmat"), type="character",
        help="Input distance matrix [required]."),
    make_option(c("-m", "--mapfile"), type="character",
        help="Input metadata mapping file [required]."),
    make_option(c("-c", "--category"), type="character",
        help="Metadata column header giving cluster IDs [required]"),
    make_option(c("-o", "--outdir"), type="character", default='.',
        help="Output directory [default %default]"),
    make_option(c("--source_dir"), type="character",
        help="Path to R source directory [required].")
)
opts <- parse_args(OptionParser(option_list = option_list), args = args)

# Error checking
if(is.null(opts$mapfile)) stop('Please supply a mapping file.')
if(is.null(opts$category)) stop('Please supply a mapping file header.')
if(is.null(opts$distmat)) stop('Please supply a distance matrix.')

# create output directory if needed
if(opts$outdir != ".") dir.create(opts$outdir,showWarnings=FALSE, recursive=TRUE)

# load qiime data
map <- load.qiime.mapping.file(opts$mapfile)
distmat <- load.qiime.distance.matrix(opts$distmat)
qiime.data <- remove.nonoverlapping.samples(map=map, distmat=distmat)

# More error checking
if(nrow(qiime.data$map) == 0)
    stop('\n\nMapping file and distance matrix have no samples in common.\n\n')
if(!is.element(opts$category, colnames(qiime.data$map))) 
    stop(sprintf('\n\nHeader %s not found in mapping file.\n\n',opts$category))

# run anosim
results <- anosim(dat=as.dist(qiime.data$distmat),grouping=qiime.data$map[[opts$category]])

# write output file
filepath <- sprintf('%s/anosim_results.txt',opts$outdir)
sink(filepath)
print(results)
sink(NULL)