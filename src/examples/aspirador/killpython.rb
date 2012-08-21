g = `ps ax | grep python`.split()
for i in g do
if i.to_i != 0
	j = i.to_i
	`kill #{j}`
end
end 
