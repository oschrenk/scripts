#!/usr/bin/env ruby
#
# Usage textile2html.rb file.textile > file.html


require "rubygems"
require "redcloth"

if ARGV[0] == nil 
	puts "No filename." 
	exit 1
end

file_name = ARGV[0]
document = IO.read(file_name)
html = RedCloth.new(document).to_html

puts eval("\"" + html + "\"")