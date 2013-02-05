function y=price_sup_dem_plot(price,sum_dem)
[category,round]=size(price);
y=price;
for i=1:5
    subplot(4,5,i);
    plot(price(i,:));
    subplot(4,5,5+i);
    bar(sum_dem(i,:));
end
for i=6:10
    subplot(4,5,5+i);
    plot(price(i,:));
    subplot(4,5,10+i);
    bar(sum_dem(i,:));
end