#!/usr/bin/env ruby
#
# Usage textile2latex .rb file.textile > file.html

require "rubygems"
require "redcloth"

if ARGV[0] == nil 
	puts "No filename." 
	exit 1
end

file_name = ARGV[0]
document = IO.read(file_name)
latex = RedCloth.new(document).to_latex

$stdout.write "#{latex}"