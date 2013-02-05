function y = normalizePrice(x)
[category,round]=size(x);
y=x;
for i=1:category
    for j=1:round
        y(i,j)=x(i,j)/x(i,1);
    end
end