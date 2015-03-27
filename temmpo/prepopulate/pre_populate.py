from browser.models import Gene
import os

def pre_populate_genes():
    """
    Pre-populate the genes from the available files
    """
    this_path = os.path.dirname(__file__)
    # I think the supplied file has integrity errors in that genes that are 
    # listed as synonyms also appear in their own right (hence the code to 
    # check we don't aalready have records)
    # wc -l  Homo_sapiens.gene_info == 
    # Gene.objects.filter(synonym_for__exact = None).count()
    file_list = ['Homo_sapiens.gene_info',]
    
    for file in file_list:   
        genefile = open("%s/%s" % (this_path, file),'r')
        
        for line in genefile:
            line = line.strip().split()
            genename = line[2]
            #print genename
            if line[4] == "-":
                synonyms = []
            else:
                synonyms = line[4].split("|")
                
            # Store gene
            if Gene.objects.filter(name = genename).exists():
                this_gene = Gene.objects.get(name = genename)
            else:
                this_gene = Gene(name = genename)
                this_gene.save()
            
            for synonym in synonyms:
                if not Gene.objects.filter(name = synonym).exists():
                    new_synonym = Gene(name = synonym,
                                       synonym_for = this_gene)
                    new_synonym.save()

#                 else:
#                     # Exists
#                     parent_gene = Gene.objects.get(name = synonym)
                    
            
        genefile.close()
    