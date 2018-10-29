#NAME:Jose Flores Martinez
#EMAIL:joseflores2395@gmail.com
#ID:404474130

import sys
import os
import csv

LEVEL1_OFFSET = 12
LEVEL2_OFFSET = 268
LEVEL3_OFFSET = 65804

min_block_num = 0
max_block_num = 0
min_inode_num = 0
max_inode_num = 0


##lists
superblock_info = ""
block_free_list = []
inode_free_list = []


##dictionaires
block_allocated_dict = {}
inode_all_dict = {}
inode_dir_dict = {}
inode_parent_dict = {2: 2} #this is for the root directory

inconsistent = False

class Inode:
    def __init__(self,i_num,links,t,allo,dir_name,parent):
        self.inode_num = i_num
        self.ref_list = []
        self.nlinks = links
        self.ptr = []
        self.file_type = t
        self.allocated = allo
        if allo == False:
            self.ptr.append((parent,i_num,dir_name))
        
        

    
class Block:
    def __init__(self,b_num,i_num,offset,lv):
        self.block_num = int(b_num)
        self.ref_list = [(int(i_num),offset,lv)]

def process_file():
    global superblock_info, block_free_list,inode_free_list,block_allocated_dict,inode_allocated_dict,min_block_num,max_block_num,min_inode_num,max_inode_num,inode_dir_dict, inode_parent_dict
    #print("Processing file")
    try:
        file = open(sys.argv[1],"r")
    except IOError as err:
        sys.stderr.write("Error with I/O: {0}\n".format(err))
        exit(1)

    reader = csv.reader(file)
    for row in reader:
        #print(row[0])
        entry_type = row[0]
        if entry_type == "BFREE":
            block_free_list.append(int(row[1]))
        elif entry_type == "IFREE":
            inode_free_list.append(int(row[1]))
        elif entry_type == "SUPERBLOCK":
            superblock_info = row
            max_block_num = int(row[1])
            min_block_num = 8
            min_inode_num = int(row[7])
            max_inode_num = int(row[6])
        elif entry_type == "INODE":
            #for the 12 direct pointers
            for offset, block in enumerate(row[12:24]):
                block = int(block)
                if block != 0:
                    #print("block--- ",block)
                    if block in block_allocated_dict:
                        block_allocated_dict[block].ref_list.append((int(row[1]),offset,0))
                    else:
                        #print(block," added to dictionary")
                        block_allocated_dict[block] = Block(block,row[1],offset,0)
            #for the next 3 indirect pointers (single,double,triple)
            if row[24] != "0":
                block = int(row[24])
                if block in block_allocated_dict:                    
                    block_allocated_dict[block].ref_list.append((int(row[1]),LEVEL1_OFFSET,1))
                else:
                    block_allocated_dict[block] = Block(row[24],row[1],LEVEL1_OFFSET,1)
            if row[25] != "0":
                block = int(row[25])
                if block in block_allocated_dict:                    
                    block_allocated_dict[block].ref_list.append((int(row[1]),LEVEL2_OFFSET,2))
                else:
                    block_allocated_dict[block] = Block(row[25],row[1],LEVEL2_OFFSET,2)
            if row[26] != "0":
                block = int(row[26])
                if block in block_allocated_dict:
                    block_allocated_dict[block].ref_list.append((int(row[1]),LEVEL3_OFFSET,3))
                else:
                    block_allocated_dict[block] = Block(row[26],row[1],LEVEL3_OFFSET,3)
            #************INODE INFO
            if row[2] == "f" or row[2] == "d" or row[2] == "0":                
                inode = int(row[1])
                if inode in inode_dir_dict:
                    inode_dir_dict[inode].allocated = True
                    inode_dir_dict[inode].nlinks = int(row[6])
                else: #not in inode_all_dict
                    inode_dir_dict[inode] = Inode(inode,int(row[6]),row[2],True,"","")
                inode_all_dict[inode] = Inode(inode,int(row[6]),row[2],True,"","")
        elif entry_type == "INDIRECT":
            block = int(row[5])
            if block in block_allocated_dict:
                block_allocated_dict[int(row[5])].ref_list.append((int(row[1]),int(row[3]),int(row[2])))
            else:
                block_allocated_dict[int(row[5])] = Block(int(row[5]),int(row[1]),int(row[3]),int(row[2]))
        elif entry_type == "DIRENT":
            inode = int(row[3])
            #print("ADDING DIRENT",inode)
            if inode in inode_dir_dict:            #vvvv parent, inode, name
                (inode_dir_dict[inode].ptr).append((int(row[1]),inode,row[6]))
                #print(inode_dir_dict[inode].ptr)
            else: #inode not in inode_dir_
                inode_dir_dict[inode] = Inode(inode,0,"d",False,row[6],int(row[1]))
            if row[6] != "'.'" and row[6] != "'..'":
                inode_parent_dict[inode] = int(row[1])
                
                
                
            
    # for key,va in block_allocated_dict.items():
    #     print(key)
    #     print(val.block_num,val.inode_num,val.offset,val.indirect_level)
    #print(superblock_info)
    #print(block_free_list)
    #print(inode_free_list)
    file.close()


def block_consistency_audits():
    global min_block_num, max_block_num, block_free_list,block_allocated_dict, inode_parent_dict,inconsistent
    #for the UNREFERENCED BLOCKS
    #AND for the ALLOCATED BLOCKS IN FREELIST
    for b in range(min_block_num,max_block_num):
        if b not in block_free_list and b not in block_allocated_dict:            
            print("UNREFERENCED BLOCK",b)
            inconsistent = True
        elif b in block_free_list and b in block_allocated_dict:
            print("ALLOCATED BLOCK",b,"ON FREELIST")
            inconsistent = True
    for key,cls in block_allocated_dict.items():
        if len(cls.ref_list) > 1:
            for ref in cls.ref_list:
                if ref[2] == 0:
                    print("DUPLICATE BLOCK",cls.block_num,"IN INODE",ref[0],"AT OFFSET",ref[1])
                    inconsistent = True
                elif ref[2] == 1:
                    print("DUPLICATE INDIRECT BLOCK",cls.block_num,"IN INODE",ref[0],"AT OFFSET",ref[1])
                    inconsistent = True
                elif ref[2] == 2:
                    print("DUPLICATE DOUBLE INDIRECT BLOCK",cls.block_num,"IN INODE",ref[0],"AT OFFSET",ref[1])
                    inconsistent = True
                elif ref[2] == 3:
                    print("DUPLICATE TRIPLE INDIRECT BLOCK",cls.block_num,"IN INODE",ref[0],"AT OFFSET",ref[1])
                    inconsistent = True
        else:
            if cls.block_num > max_block_num - 1:
                if cls.ref_list[0][2] == 0:
                    print("INVALID BLOCK",cls.block_num,"IN INODE",cls.ref_list[0][0],"AT OFFSET", cls.ref_list[0][1])
                    inconsistent = True
                elif cls.ref_list[0][2] == 1:
                    print("INVALID INDIRECT BLOCK",cls.block_num,"IN INODE",cls.ref_list[0][0],"AT OFFSET", cls.ref_list[0][1])
                    inconsistent = True
                elif cls.ref_list[0][2] == 2:
                    print("INVALID DOUBLE INDIRECT BLOCK",cls.block_num,"IN INODE",cls.ref_list[0][0],"AT OFFSET", cls.ref_list[0][1])
                    inconsistent = True
                elif cls.ref_list[0][2] == 3:
                    print("INVALID TRIPLE INDIRECT BLOCK",cls.block_num,"IN INODE",cls.ref_list[0][0],"AT OFFSET", cls.ref_list[0][1])
                    inconsistent = True
            if cls.block_num < min_block_num:
                if cls.ref_list[0][2] == 0:
                    print("RESERVED BLOCK",cls.block_num,"IN INODE",cls.ref_list[0][0],"AT OFFSET", cls.ref_list[0][1])
                    inconsistent = True
                elif cls.ref_list[0][2] == 1:
                    print("RESERVED INDIRECT BLOCK",cls.block_num,"IN INODE",cls.ref_list[0][0],"AT OFFSET", cls.ref_list[0][1])
                    inconsistent = True
                elif cls.ref_list[0][2] == 2:
                    print("RESERVED DOUBLE INDIRECT BLOCK",cls.block_num,"IN INODE",cls.ref_list[0][0],"AT OFFSET", cls.ref_list[0][1])
                    inconsistent = True
                elif cls.ref_list[0][2] == 3:
                    print("RESERVED TRIPLE INDIRECT BLOCK",cls.block_num,"IN INODE",cls.ref_list[0][0],"AT OFFSET", cls.ref_list[0][1])
                    inconsistent = True
                    
                
def inode_allocation_audits():
    global min_inode_num,max_inode_num,inode_free_list,inode_all_dict, inode_parent_dict,inconsistent
    #print("MIN INODE:",min_inode_num,"-- MAX INODE",max_inode_num)
    for i in range(min_inode_num,max_inode_num):
        if i not in inode_free_list and i not in inode_all_dict:
            print("UNALLOCATED INODE",i,"NOT ON FREELIST")
            inconsistent = True
    for key,cls in inode_all_dict.items():
        if cls.inode_num in inode_free_list:
            print("ALLOCATED INODE",cls.inode_num,"ON FREELIST")
            inconsistent = True


def inode_directory_audits():
    global min_inode_num,max_inode_num,inode_dir_dict,inode_parent_dict,inconsistent
    #print(inode_parent_dict)
    #print(min_inode_num,"----",max_inode_num)
    # for key,cls in inode_dir_dict.items():
    #        print(key,cls.ptr)
    for key,cls in inode_dir_dict.items():
        ptr_len = len(cls.ptr)
        nlinks_len =cls.nlinks        
        inode = cls.inode_num
        valid = True if (key>=min_inode_num and (key<max_inode_num-1)) else False
        dot_dir = cls.ptr
        if ptr_len != nlinks_len and valid:
            if nlinks_len != 0: #link counts error
                print("INODE",inode,"HAS",ptr_len,"LINKS BUT LINKCOUNT IS",nlinks_len)
                inconsistent = True
            else: #unallocated error
                for tup in cls.ptr:
                    print("DIRECTORY INODE",tup[0],"NAME",tup[2],"UNALLOCATED INODE",tup[1])
                    inconsistent = True
        if valid == False and inode != 2:
            for tup in cls.ptr:
                print("DIRECTORY INODE",tup[0],"NAME",tup[2],"INVALID INODE",tup[1])
                inconsistent = True
        #check inode 2 which is reserved for root directory
        if inode == 2:
            if nlinks_len != ptr_len:
                print("INODE",inode,"HAS",ptr_len,"LINKS BUT LINKCOUNT IS",nlinks_len)
                inconsistent = True
        for tup in dot_dir:
            #print(tup[0],tup[1],tup[2])            
            if tup[2] == "'.'":
                if tup[0] != tup[1]:
                    #print(inode,tup)
                    print("DIRECTORY INODE",tup[0],"NAME",tup[2],"LINK TO NODE",tup[1],"SHOULD BE",tup[0])
                    inconsistent = True
            if tup[2] == "'..'":
                if inode != inode_parent_dict[tup[0]]:
                    #print(tup)
                    print("DIRECTORY INODE",tup[0],"NAME",tup[2],"LINK TO INODE",inode,"SHOULD BE",tup[0])
                    inconsistent = True
    
def main():
    global min_block_num, max_block_num
    if len(sys.argv) != 2:
        sys.stderr.write("Error: Invalid number of arguements. Expected 1\n")
        exit(1)

    process_file()
    block_consistency_audits()
    inode_allocation_audits()
    inode_directory_audits()

    if inconsistent == True:
        #sys.stderr.write("inconsistent")
        exit(2)
        
    exit(0)
    
if __name__ == "__main__":
    main()
